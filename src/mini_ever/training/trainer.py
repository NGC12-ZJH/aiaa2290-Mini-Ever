"""Training loops: ArcFace classification, embedding extraction and distillation."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, Dataset

from mini_ever.utils.seeding import seed_everything
from mini_ever.utils.timing import Stopwatch


@dataclass(frozen=True)
class OptimSpec:
    """Everything needed to run one training loop."""

    epochs: int
    learning_rate: float
    batch_size: int
    optimizer: str = "sgd"
    weight_decay: float = 5e-4
    momentum: float = 0.9
    scheduler: str = "cosine"
    amp: bool = True
    num_workers: int = 0

    def __post_init__(self) -> None:
        if self.optimizer not in ("sgd", "adamw"):
            raise ValueError("optimizer must be 'sgd' or 'adamw'")
        if self.scheduler not in ("cosine", "constant"):
            raise ValueError("scheduler must be 'cosine' or 'constant'")


@dataclass
class TrainReport:
    seconds: float = 0.0
    steps: int = 0
    epoch_losses: list[float] = field(default_factory=list)


def select_device(preferred: str | None = None) -> torch.device:
    if preferred:
        return torch.device(preferred)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def make_loader(
    dataset: Dataset, batch_size: int, shuffle: bool, seed: int, num_workers: int = 0, drop_last: bool = False
) -> DataLoader:
    generator = torch.Generator()
    generator.manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=drop_last and len(dataset) > batch_size,  # type: ignore[arg-type]
        num_workers=num_workers,
        generator=generator,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=num_workers > 0,
    )


def make_optimizer(parameters, spec: OptimSpec) -> torch.optim.Optimizer:
    if spec.optimizer == "sgd":
        return torch.optim.SGD(
            parameters, lr=spec.learning_rate, momentum=spec.momentum, weight_decay=spec.weight_decay
        )
    return torch.optim.AdamW(parameters, lr=spec.learning_rate, weight_decay=spec.weight_decay)


def make_scheduler(optimizer: torch.optim.Optimizer, spec: OptimSpec, total_steps: int):
    if spec.scheduler == "constant":
        return torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    return torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda step: 0.5 * (1.0 + math.cos(math.pi * min(step, total_steps) / max(1, total_steps)))
    )


StepLoss = Callable[[nn.Module, torch.Tensor, torch.Tensor], torch.Tensor]


def arcface_loss(model: nn.Module, images: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    return F.cross_entropy(model.logits(images, labels), labels)


def train_loop(
    model: nn.Module,
    dataset: Dataset,
    spec: OptimSpec,
    device: torch.device,
    seed: int,
    loss_fn: StepLoss = arcface_loss,
    parameters=None,
) -> TrainReport:
    """Generic supervised loop (SGD/AdamW, cosine schedule, optional AMP).

    ``loss_fn(model, images, labels)`` returns the scalar loss for one batch.
    """
    seed_everything(seed)
    model.to(device).train()
    loader = make_loader(dataset, spec.batch_size, True, seed, spec.num_workers, drop_last=True)
    optimizer = make_optimizer(parameters if parameters is not None else model.parameters(), spec)
    total = spec.epochs * len(loader)
    scheduler = make_scheduler(optimizer, spec, total)
    use_amp = spec.amp and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    report = TrainReport()
    with Stopwatch() as watch:
        for _ in range(spec.epochs):
            running, batches = 0.0, 0
            for images, labels, _ in loader:
                images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
                with torch.autocast(device.type, enabled=use_amp):
                    loss = loss_fn(model, images, labels)
                optimizer.zero_grad(set_to_none=True)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                running += loss.item()
                batches += 1
                report.steps += 1
            report.epoch_losses.append(running / max(1, batches))
    report.seconds = watch.seconds
    model.eval()
    return report


@torch.no_grad()
def embed_dataset(model: nn.Module, dataset: Dataset, device: torch.device, batch_size: int = 256) -> np.ndarray:
    """L2-normalised embeddings, in dataset order. ``model`` must expose ``embed``."""
    model.to(device).eval()
    loader = make_loader(dataset, batch_size, shuffle=False, seed=0)
    chunks = [model.embed(images.to(device)).float().cpu() for images, _, _ in loader]
    if not chunks:
        return np.zeros((0, 0), dtype=np.float32)
    return torch.cat(chunks).numpy()


@torch.no_grad()
def predict_dataset(model: nn.Module, dataset: Dataset, device: torch.device, batch_size: int = 256) -> np.ndarray:
    """Identity predicted by the classifier for each image (test level L1)."""
    model.to(device).eval()
    loader = make_loader(dataset, batch_size, shuffle=False, seed=0)
    chunks = [model.predict_identity(images.to(device)).cpu() for images, _, _ in loader]
    return torch.cat(chunks).numpy() if chunks else np.zeros(0, dtype=np.int64)


def distill_embeddings(
    teacher: nn.Module,
    student: nn.Module,
    dataset: Dataset,
    spec: OptimSpec,
    device: torch.device,
    seed: int,
) -> TrainReport:
    """Train ``student.embed`` to match ``teacher.embed`` (cosine loss).

    The distillation set never contains forget identities (protocol), so any
    influence that reaches the student must travel *through the teacher*.
    """
    teacher.to(device).eval()

    def loss_fn(model: nn.Module, images: torch.Tensor, _labels: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            target = teacher.embed(images)
        return (1.0 - (model.embed(images) * target).sum(dim=1)).mean()

    return train_loop(student, dataset, spec, device, seed, loss_fn, parameters=student.backbone.parameters())
