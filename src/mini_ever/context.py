"""Experiment context: one object that knows the config, the manifest, the data
and every trained model, and caches models on disk.

Experiments ask the context for *what* they need ("the main model for seed 3",
"the person reference for forget group 0") and the context decides whether to
load it from ``runs/models`` or train it. Cache keys contain everything that
changes the weights (relevant config sections, manifest hash, canary plan,
removed photos, seed, backbone), so a stale model is never reused.

Seeds
-----
Evaluated models use the training seeds from the config. Reference models use
a *derived* seed (:meth:`Context.reference_seed`), so that "exact retraining"
is compared with an independently trained reference and the comparison shows
real seed-to-seed noise instead of a trivially identical model.
"""

from __future__ import annotations

import platform
import subprocess
import weakref
from collections import OrderedDict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from mini_ever.config import ExperimentConfig
from mini_ever.data.canary import CanaryPlan, Trigger, plan_canaries
from mini_ever.data.datasets import (
    CELEBA_ALIGNED_CROP,
    FaceDataset,
    FolderImageLoader,
    ImageLoader,
    build_transforms,
)
from mini_ever.data.deletion import (
    account_removed,
    person_removed,
    stage1_training_records,
    stage2_training_records,
)
from mini_ever.data.lfw import LFW_CENTER_CROP, LfwPair, read_name_list, read_pairs
from mini_ever.data.splits import GALLERY, TEST, ImageRecord, LabelSpace, SplitManifest
from mini_ever.models.artifacts import ArtifactRegistry
from mini_ever.models.backbones import EmbeddingNet
from mini_ever.models.face_model import FaceModel, FeatureExtractor, build_face_model, with_new_head
from mini_ever.models.gallery import Gallery
from mini_ever.training.trainer import OptimSpec, distill_embeddings, embed_dataset, select_device, train_loop
from mini_ever.utils.hashing import sha256_json, sha256_state_dict, sha256_strings
from mini_ever.utils.io import read_json, write_json
from mini_ever.utils.seeding import derive_seed


# How many models the in-memory cache keeps (each ResNet-50 is ~100 MB on the GPU).
MEMORY_MODELS = 16


class Context:
    def __init__(
        self,
        config: ExperimentConfig,
        manifest: SplitManifest,
        image_loader: ImageLoader,
        *,
        device: str | None = None,
        crop_box: tuple[int, int, int, int] | None = CELEBA_ALIGNED_CROP,
        allow_incomplete: bool = False,
    ) -> None:
        config.validate()
        if not allow_incomplete:
            config.require_complete()
        self.config = config
        self.manifest = manifest
        self.loader = image_loader
        self.device = select_device(device)
        self.runs_dir = Path(config.paths.runs_dir)
        self.results_dir = Path(config.paths.results_dir)
        self.registry = ArtifactRegistry(
            self.runs_dir / "artifacts.json" if config.tracking.artifact_manifest else None
        )
        self.canary: CanaryPlan | None = plan_canaries(manifest, config.canary)
        self.labels1: LabelSpace = manifest.stage1_labels()
        self.labels2: LabelSpace = manifest.stage2_labels()
        self.train_transforms = build_transforms(config.model.input_size, train=True, crop_box=crop_box)
        self.eval_transforms = build_transforms(config.model.input_size, train=False, crop_box=crop_box)
        # Recently used models stay in (GPU) memory; older ones are dropped and
        # reloaded from disk on demand, so long runs (exp03 shadows) do not
        # exhaust GPU memory. ``_artifact_of`` holds a weak reference next to
        # each id so a recycled ``id()`` never maps a new model to an old artifact.
        self._models: OrderedDict[str, nn.Module] = OrderedDict()
        self._artifact_of: dict[int, tuple[weakref.ref, str]] = {}
        self._embeddings: dict[tuple[str, str], np.ndarray] = {}
        self._train_seconds: dict[str, float] = {}

    @classmethod
    def from_config(cls, config: ExperimentConfig, **kwargs: Any) -> Context:
        """Real-data context: manifest and images come from the paths in the config."""
        manifest = SplitManifest.load(config.data.manifest_path)
        loader = FolderImageLoader(Path(config.data.local_root) / config.data.image_dir)
        return cls(config, manifest, loader, **kwargs)

    # ------------------------------------------------------------------ #
    # Seeds and optimiser settings
    # ------------------------------------------------------------------ #

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(self.config.data.training_seeds)

    @staticmethod
    def reference_seed(seed: int) -> int:
        return derive_seed(seed, "reference")

    def stage_spec(self, stage: int) -> OptimSpec:
        t = self.config.training
        epochs = t.stage1_epochs if stage == 1 else t.stage2_epochs
        return OptimSpec(
            epochs=int(epochs),  # type: ignore[arg-type]
            learning_rate=float(t.learning_rate),  # type: ignore[arg-type]
            batch_size=int(t.batch_size),  # type: ignore[arg-type]
            optimizer=str(t.optimizer),
            weight_decay=t.weight_decay,
            momentum=t.momentum,
            scheduler=t.scheduler,
            amp=t.amp,
            num_workers=t.num_workers,
        )

    def distill_spec(self) -> OptimSpec:
        d, t = self.config.distill, self.config.training
        return OptimSpec(
            epochs=int(d.epochs),  # type: ignore[arg-type]
            learning_rate=float(d.learning_rate),  # type: ignore[arg-type]
            batch_size=int(d.batch_size),  # type: ignore[arg-type]
            optimizer=str(t.optimizer),
            weight_decay=t.weight_decay,
            momentum=t.momentum,
            amp=t.amp,
            num_workers=t.num_workers,
        )

    def unlearning_spec(self, epochs: int, scheduler: str = "constant") -> OptimSpec:
        u, t = self.config.unlearning, self.config.training
        return OptimSpec(
            epochs=int(epochs),
            learning_rate=float(u.learning_rate),  # type: ignore[arg-type]
            batch_size=int(u.batch_size),  # type: ignore[arg-type]
            optimizer=str(t.optimizer),
            weight_decay=t.weight_decay,
            momentum=t.momentum,
            scheduler=scheduler,
            amp=t.amp,
            num_workers=t.num_workers,
        )

    # ------------------------------------------------------------------ #
    # Datasets
    # ------------------------------------------------------------------ #

    def train_dataset(self, records: Sequence[ImageRecord], labels: LabelSpace) -> FaceDataset:
        """Training data: augmented, with canaries stamped where planned."""
        return FaceDataset(records, self.loader, self.train_transforms, labels, canary=self.canary)

    def eval_dataset(
        self,
        records: Sequence[ImageRecord],
        labels: LabelSpace | None = None,
        trigger: Trigger | None = None,
    ) -> FaceDataset:
        """Evaluation data: no augmentation, no canaries unless ``trigger`` is forced."""
        return FaceDataset(records, self.loader, self.eval_transforms, labels, force_trigger=trigger)

    def records(self, role: str, identities: Iterable[int]) -> list[ImageRecord]:
        return self.manifest.select(role=role, identities=identities)

    # ------------------------------------------------------------------ #
    # Models (cached)
    # ------------------------------------------------------------------ #

    def artifact_id(self, model: nn.Module) -> str | None:
        entry = self._artifact_of.get(id(model))
        if entry is None or entry[0]() is not model:
            return None
        return entry[1]

    def _remember(self, artifact_id: str, model: nn.Module, keep: bool = True) -> None:
        self._artifact_of[id(model)] = (weakref.ref(model), artifact_id)
        if not keep:
            return
        self._models[artifact_id] = model
        self._models.move_to_end(artifact_id)
        while len(self._models) > MEMORY_MODELS:
            self._models.popitem(last=False)

    def _cache_key(self, parts: dict[str, Any]) -> str:
        base = {
            "manifest": self.manifest.hash(),
            "canary": self.canary.hash() if self.canary else None,
            "model": asdict(self.config.model),
            "training": asdict(self.config.training),
        }
        return sha256_json({**base, **parts})[:16]

    def cached_model(
        self,
        name: str,
        parts: dict[str, Any],
        factory: Callable[[], nn.Module],
        train: Callable[[nn.Module], Any],
        register: Callable[[str, nn.Module], None],
    ) -> nn.Module:
        """Return model ``name`` for ``parts``: memory -> disk -> train.

        ``factory`` builds an untrained model of the right shape, ``train``
        trains it in place and returns a report, ``register`` records it in
        the artifact manifest.
        """
        artifact_id = f"{name}-{self._cache_key(parts)}"
        if artifact_id in self._models:
            self._models.move_to_end(artifact_id)
            return self._models[artifact_id]
        path = self.runs_dir / "models" / f"{artifact_id}.pt"
        model = factory()
        if path.exists():
            model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
            model.to(self.device).eval()
            self._train_seconds[artifact_id] = float(read_json(path.with_suffix(".json"))["train_report"]["seconds"])
        else:
            report = train(model)
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), path)
            write_json(path.with_suffix(".json"), {"artifact_id": artifact_id, "parts": parts, "train_report": report})
            register(artifact_id, model)
            self._train_seconds[artifact_id] = float(report.seconds)
        self._remember(artifact_id, model)
        return model

    def train_seconds(self, model: nn.Module) -> float:
        """Wall-clock seconds it took to train a cached model (read back from disk if needed)."""
        return self._train_seconds[self.artifact_id(model) or ""]

    def register_trained(self, kind: str, records: Sequence[ImageRecord], parents: Iterable[str], notes: str = ""):
        def register(artifact_id: str, model: nn.Module) -> None:
            self.registry.register(
                artifact_id,
                kind,
                identities={r.identity for r in records},
                accounts={r.account for r in records},
                parents=parents,
                weights_sha256=sha256_state_dict(model.state_dict()),
                notes=notes,
            )

        return register

    def imagenet_init(self, backbone: str | None = None) -> FeatureExtractor:
        """Untrained starting point (Experiment 0). Uses pooled ImageNet features."""
        net = EmbeddingNet(
            backbone or self.config.model.backbone, self.config.model.embedding_dim, self.config.model.initialization
        )
        model = FeatureExtractor(net).to(self.device).eval()
        self._remember(f"init-{backbone or self.config.model.backbone}", model, keep=False)
        return model

    def public_base(self, backbone: str | None = None) -> FaceModel:
        """Stage 1: trained once on the public pool, shared by every stage-2 model."""
        backbone = backbone or self.config.model.backbone
        records = stage1_training_records(self.manifest)
        seed = derive_seed(self.seeds[0], "public_base")
        return self.cached_model(  # type: ignore[return-value]
            "public_base",
            {"backbone": backbone, "seed": seed},
            factory=lambda: build_face_model(self.config.model, self.labels1.identities, backbone),
            train=lambda m: train_loop(
                m, self.train_dataset(records, self.labels1), self.stage_spec(1), self.device, seed
            ),
            register=self.register_trained("public_base", records, ()),
        )

    def stage2(self, removed: frozenset[str], seed: int, backbone: str | None = None, kind: str = "main") -> FaceModel:
        """Stage 2 from the public base on public + user photos minus ``removed``."""
        backbone = backbone or self.config.model.backbone
        base = self.public_base(backbone)
        records = stage2_training_records(self.manifest, removed)
        return self.cached_model(  # type: ignore[return-value]
            "stage2",
            {"backbone": backbone, "seed": seed, "removed": sha256_strings(removed)},
            factory=lambda: with_new_head(base, self.config.model, self.labels2.identities),
            train=lambda m: train_loop(
                m, self.train_dataset(records, self.labels2), self.stage_spec(2), self.device, seed
            ),
            register=self.register_trained(kind, records, (self.artifact_id(base) or "",)),
        )

    def main_model(self, seed: int, backbone: str | None = None) -> FaceModel:
        return self.stage2(frozenset(), seed, backbone, kind="main")

    def person_reference(self, identities: Iterable[int], seed: int, backbone: str | None = None) -> FaceModel:
        """Never saw any photo of ``identities`` (the default yardstick for forgetting)."""
        removed = person_removed(self.manifest, identities)
        return self.stage2(removed, self.reference_seed(seed), backbone, kind="reference")

    def account_reference(self, identities: Iterable[int], seed: int, backbone: str | None = None) -> FaceModel:
        """Never saw the photos uploaded by these users' own accounts."""
        removed = account_removed(self.manifest, identities)
        return self.stage2(removed, self.reference_seed(seed), backbone, kind="reference")

    def distillation_records(self) -> list[ImageRecord]:
        """Training photos of identities that are in no forget group (protocol)."""
        excluded = self.manifest.forget_union
        return [r for r in stage2_training_records(self.manifest) if r.identity not in excluded]

    def student(self, teacher: nn.Module, seed: int) -> FaceModel:
        """Downstream student distilled from ``teacher`` on forget-free data."""
        teacher_id = self.artifact_id(teacher)
        if teacher_id is None:
            raise ValueError("register the teacher first (use context-built models)")
        records = self.distillation_records()
        backbone = self.config.distill.student_backbone
        dim = int(teacher.embedding_dim)  # a SISA ensemble has wider embeddings than one model
        return self.cached_model(  # type: ignore[return-value]
            "student",
            {"teacher": teacher_id, "seed": seed, "backbone": backbone, "distill": asdict(self.config.distill)},
            factory=lambda: build_face_model(
                self.config.model, self.labels2.identities, backbone, embedding_dim=dim
            ),
            train=lambda m: distill_embeddings(
                teacher, m, self.train_dataset(records, self.labels2), self.distill_spec(), self.device, seed
            ),
            register=self.register_trained("student", records, (teacher_id,), notes="distilled"),
        )

    def adopt(self, model: nn.Module, artifact_id: str, kind: str, parents: Iterable[str], notes: str = "") -> None:
        """Register a model built outside the cache (unlearned or quantised copies)."""
        parent_ids = tuple(parents)
        self._remember(artifact_id, model)
        self.registry.register(
            artifact_id,
            kind,
            identities=(),
            accounts=(),
            parents=parent_ids,
            weights_sha256=sha256_state_dict(model.state_dict()),
            notes=notes,
        )

    # ------------------------------------------------------------------ #
    # Embeddings and galleries
    # ------------------------------------------------------------------ #

    def embed(self, model: nn.Module, records: Sequence[ImageRecord], trigger: Trigger | None = None) -> np.ndarray:
        """Embeddings of ``records`` under ``model`` (memoised for registered models)."""
        model_id = self.artifact_id(model)
        key = (
            model_id or f"anon-{id(model)}",
            sha256_json([[r.image_id for r in records], None if trigger is None else trigger.group_index]),
        )
        if model_id is not None and key in self._embeddings:
            return self._embeddings[key]
        embeddings = embed_dataset(model, self.eval_dataset(records, trigger=trigger), self.device)
        if model_id is not None:
            self._embeddings[key] = embeddings
        return embeddings

    def gallery(self, model: nn.Module, exclude: Iterable[int] = ()) -> Gallery:
        """Gallery of every identity's enrollment photos, minus ``exclude``."""
        excluded = set(exclude)
        records = [r for r in self.manifest.select(role=GALLERY) if r.identity not in excluded]
        embeddings = self.embed(model, records)
        return Gallery(embeddings, np.asarray([r.identity for r in records]), tuple(r.image_id for r in records))

    def audit_records(self, identities: Iterable[int]) -> list[ImageRecord]:
        """Independent audit photos (the ``test`` role) of ``identities``."""
        return self.records(TEST, identities)

    # ------------------------------------------------------------------ #
    # LFW
    # ------------------------------------------------------------------ #

    def lfw_pairs(self) -> list[LfwPair] | None:
        """LFW pairs minus excluded names, or ``None`` if LFW is not available locally."""
        ev = self.config.evaluation
        path = Path(ev.lfw_root) / ev.lfw_pairs_file
        if not path.exists():
            return None
        return read_pairs(path, read_name_list(ev.lfw_excluded_names_file))

    def lfw_loader(self) -> tuple[ImageLoader, Any]:
        loader = FolderImageLoader(self.config.evaluation.lfw_root)
        return loader, build_transforms(self.config.model.input_size, train=False, crop_box=LFW_CENTER_CROP)

    # ------------------------------------------------------------------ #
    # Results
    # ------------------------------------------------------------------ #

    def run_metadata(self) -> dict[str, Any]:
        """Protocol "最小运行记录" fields shared by every result file."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_commit": _git_commit(),
            "config_sha256": self.config.hash(),
            "manifest_sha256": self.manifest.hash(),
            "canary_sha256": self.canary.hash() if self.canary else None,
            "training_seeds": list(self.seeds),
            "device": str(self.device),
            "torch": torch.__version__,
            "python": platform.python_version(),
        }

    def save_result(self, experiment: str, payload: dict[str, Any]) -> Path:
        """Write ``results/<experiment>/<timestamp>.json`` (local; contains no identity ids)."""
        meta = self.run_metadata()
        stamp = meta["timestamp"].replace(":", "").replace("-", "")
        return write_json(self.results_dir / experiment / f"{stamp}.json", {"meta": meta, **payload})


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
