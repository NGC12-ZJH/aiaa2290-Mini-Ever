"""Approximate unlearning: change the trained model instead of retraining.

* **Output filter** - hide the person's name from the classifier output. No
  parameter changes; this is the "shortcut" that can pass L1 and nothing else.
* **FT** - keep training on the retain set only and hope the forget set fades.
* **NegGrad+** - gradient *ascent* on the forget set balanced with descent on
  the retain set (Kurmanji et al., 2023 baseline).
* **SCRUB** - Kurmanji et al. (NeurIPS 2023): a student starts as a copy of
  the model and alternates "max" steps that push it *away* from the frozen
  teacher on the forget set with "min" steps that keep it *close* to the
  teacher (plus cross-entropy) on the retain set.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterable

import torch
import torch.nn.functional as F
from torch import nn

from mini_ever.context import Context
from mini_ever.models.face_model import FaceModel
from mini_ever.training.trainer import arcface_loss, make_loader, make_optimizer, train_loop
from mini_ever.unlearning.base import UnlearningOutput, forget_and_retain
from mini_ever.utils.seeding import derive_seed, seed_everything
from mini_ever.utils.timing import Stopwatch


def output_filter(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    filtered = copy.deepcopy(model)
    assert isinstance(filtered, FaceModel)
    with Stopwatch() as watch:
        filtered.block(identities)
    return UnlearningOutput(filtered, "output_filter", watch.seconds, exact=False, notes="parameters unchanged")


def finetune(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    _, retain = forget_and_retain(ctx, removed)
    student = copy.deepcopy(model)
    spec = ctx.unlearning_spec(int(ctx.config.unlearning.finetune_epochs))  # type: ignore[arg-type]
    report = train_loop(student, ctx.train_dataset(retain, ctx.labels2), spec, ctx.device, derive_seed(seed, "ft"))
    return UnlearningOutput(student, "finetune", report.seconds, exact=False)


def neggrad_plus(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    """Loss per step: ``alpha * CE(retain) - (1 - alpha) * CE(forget)``."""
    forget, retain = forget_and_retain(ctx, removed)
    alpha = ctx.config.unlearning.neggrad_alpha
    spec = ctx.unlearning_spec(int(ctx.config.unlearning.neggrad_epochs))  # type: ignore[arg-type]
    run_seed = derive_seed(seed, "neggrad")
    seed_everything(run_seed)

    student = copy.deepcopy(model).to(ctx.device).train()
    retain_loader = make_loader(ctx.train_dataset(retain, ctx.labels2), spec.batch_size, True, run_seed, spec.num_workers, True)
    forget_loader = make_loader(ctx.train_dataset(forget, ctx.labels2), spec.batch_size, True, run_seed + 1, spec.num_workers)
    forget_batches = itertools.cycle(forget_loader)
    optimizer = make_optimizer(student.parameters(), spec)

    with Stopwatch() as watch:
        for _ in range(spec.epochs):
            for images, labels, _ in retain_loader:
                f_images, f_labels, _ = next(forget_batches)
                retain_loss = arcface_loss(student, images.to(ctx.device), labels.to(ctx.device))
                forget_logits = student.logits(f_images.to(ctx.device))
                forget_loss = F.cross_entropy(forget_logits, f_labels.to(ctx.device))
                loss = alpha * retain_loss - (1.0 - alpha) * forget_loss
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
    student.eval()
    return UnlearningOutput(student, "neggrad_plus", watch.seconds, exact=False)


def _kl(teacher_logits: torch.Tensor, student_logits: torch.Tensor, temperature: float) -> torch.Tensor:
    """KL(teacher || student) on temperature-softened distributions."""
    return F.kl_div(
        F.log_softmax(student_logits / temperature, dim=1),
        F.softmax(teacher_logits / temperature, dim=1),
        reduction="batchmean",
    ) * temperature**2


def scrub(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    forget, retain = forget_and_retain(ctx, removed)
    u = ctx.config.unlearning
    spec = ctx.unlearning_spec(int(u.scrub_epochs))  # type: ignore[arg-type]
    run_seed = derive_seed(seed, "scrub")
    seed_everything(run_seed)

    teacher = copy.deepcopy(model).to(ctx.device).eval()
    student = copy.deepcopy(model).to(ctx.device).train()
    optimizer = make_optimizer(student.parameters(), spec)
    retain_loader = make_loader(ctx.train_dataset(retain, ctx.labels2), spec.batch_size, True, run_seed, spec.num_workers, True)
    forget_loader = make_loader(ctx.train_dataset(forget, ctx.labels2), spec.batch_size, True, run_seed + 1, spec.num_workers)

    with Stopwatch() as watch:
        for epoch in range(spec.epochs):
            # "max" steps (first ``scrub_max_epochs`` epochs only): move away
            # from the teacher on the forget set.
            if epoch < u.scrub_max_epochs:
                for images, _, _ in forget_loader:
                    images = images.to(ctx.device)
                    with torch.no_grad():
                        target = teacher.logits(images)
                    loss = -_kl(target, student.logits(images), u.scrub_temperature)
                    optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    optimizer.step()
            # "min" steps: stay close to the teacher and accurate on the retain set.
            for images, labels, _ in retain_loader:
                images, labels = images.to(ctx.device), labels.to(ctx.device)
                with torch.no_grad():
                    target = teacher.logits(images)
                student_logits = student.logits(images)
                loss = u.scrub_alpha * _kl(target, student_logits, u.scrub_temperature) + arcface_loss(
                    student, images, labels
                )
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
    student.eval()
    return UnlearningOutput(student, "scrub", watch.seconds, exact=False)
