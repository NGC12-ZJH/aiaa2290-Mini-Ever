"""Typed experiment configuration.

The configuration lives in a JSON file (see ``configs/base.json``). This module
turns it into frozen dataclasses so that every field is named, typed and
documented in one place, and so that typos in the JSON fail loudly instead of
being silently ignored.

A value of ``null`` in the JSON means "this is a research decision that must be
fixed before a real run". :func:`ExperimentConfig.missing_fields` lists those
fields and :func:`ExperimentConfig.require_complete` refuses to continue while
any of them is still open.
"""

from __future__ import annotations

import dataclasses
import json
import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mini_ever.utils.hashing import sha256_json

# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PoolConfig:
    """Share of selected identities in the public pool and the user pool."""

    public: float = 0.4
    user: float = 0.6


@dataclass(frozen=True)
class SplitRatios:
    """Per-identity split of images into train / gallery (enrollment) / test (audit)."""

    train: float = 0.7
    gallery: float = 0.1
    test: float = 0.2


@dataclass(frozen=True)
class AccountConfig:
    """How each user-pool identity's training photos are spread over uploader accounts."""

    self_share: float = 0.6
    other_uploaders_per_identity: int = 2
    other_uploaders_are_virtual: bool = True


@dataclass(frozen=True)
class DataConfig:
    dataset: str = "CelebA"
    local_root: str = "data/celeba"
    image_dir: str = "img_align_celeba"
    identity_file: str = "identity_CelebA.txt"
    min_images_per_identity: int = 25
    target_identities: int = 1000
    identity_pools: PoolConfig = field(default_factory=PoolConfig)
    split_ratios: SplitRatios = field(default_factory=SplitRatios)
    accounts: AccountConfig = field(default_factory=AccountConfig)
    forget_pool: str = "user"
    forget_units: tuple[str, ...] = ("account", "person")
    forget_identities_per_group: int = 20
    forget_group_count: int | None = None
    split_seed: int | None = None
    account_seed: int | None = None
    training_seeds: tuple[int, ...] = ()
    manifest_path: str = "data/splits/manifest.json"


@dataclass(frozen=True)
class ModelConfig:
    backbone: str = "resnet50"
    initialization: str = "imagenet_pretrained"
    forbid_face_pretrained_weights: bool = True
    init_weights_source: str | None = None
    init_weights_sha256: str | None = None
    input_size: tuple[int, int] = (112, 112)
    embedding_dim: int = 512
    loss: str = "arcface"
    arcface_scale: float = 64.0
    arcface_margin: float = 0.5


@dataclass(frozen=True)
class TrainingConfig:
    two_stage: bool = True
    stage1_data: str = "public_pool"
    stage2_data: str = "public_pool_plus_user_pool"
    stage1_epochs: int | None = None
    stage2_epochs: int | None = None
    optimizer: str | None = None
    learning_rate: float | None = None
    batch_size: int | None = None
    weight_decay: float = 5e-4
    momentum: float = 0.9
    scheduler: str = "cosine"
    amp: bool = True
    num_workers: int = 4


@dataclass(frozen=True)
class SisaConfig:
    shard_counts: tuple[int, ...] = (4, 8, 16)
    partition_unit: str = "identity"
    partitioned_pool: str = "user"
    shard_initialization: str = "public_base_model"
    include_public_pool_in_shards: bool | None = None
    backbone: str = "resnet18"
    embedding_aggregation: str = "concatenate_normalized"
    slicing_enabled: bool = False
    sequential_requests: int = 20
    full_chain_every: int = 1


@dataclass(frozen=True)
class TrackingConfig:
    artifact_manifest: bool = True
    archive_checkpoints: bool = True


@dataclass(frozen=True)
class CanaryConfig:
    """Athena-style trigger patterns stamped on some forget-identity training photos."""

    enabled: bool = True
    fraction_of_forget_train_images: float = 0.2
    patch_fraction: float = 0.15
    seed: int | None = None


@dataclass(frozen=True)
class DistillConfig:
    student_backbone: str = "resnet18"
    epochs: int | None = None
    learning_rate: float | None = None
    batch_size: int | None = None


@dataclass(frozen=True)
class UnlearningConfig:
    learning_rate: float | None = None
    batch_size: int | None = None
    finetune_epochs: int | None = None
    neggrad_epochs: int | None = None
    neggrad_alpha: float = 0.99
    scrub_epochs: int | None = None
    scrub_max_epochs: int = 1
    scrub_alpha: float = 0.1
    scrub_temperature: float = 4.0


@dataclass(frozen=True)
class PriorCheckConfig:
    models: tuple[str, ...] = ("imagenet_init", "public_base")
    comparisons: tuple[str, ...] = ("forget_vs_other_user", "public_vs_user_positive_control")
    metrics: tuple[str, ...] = ("verification_tar_at_far", "retrieval_top1")
    equivalence_margin: float | None = None


@dataclass(frozen=True)
class EvaluationConfig:
    reference: str = "matched_never_trained"
    reference_types: tuple[str, ...] = ("person", "account")
    prior_familiarity_check: PriorCheckConfig = field(default_factory=PriorCheckConfig)
    quantization_bits: tuple[int, ...] = (8, 4)
    quantization_scheme: str = "weight_only_rtn"
    relearning_images_per_forget_identity: int = 5
    relearning_steps: int = 50
    relearning_eval_every: int = 10
    trace_miss_rates: tuple[float, ...] = (0.0, 0.05, 0.2, 0.4)
    trace_miss_seed: int | None = None
    shadow_model_count: int | None = None
    equivalence_margins: dict[str, float] | None = None
    confidence_level: float | None = None
    bootstrap_samples: int = 2000
    far_target: float = 1e-3
    lfw_root: str = "data/lfw"
    lfw_pairs_file: str = "pairs.txt"
    lfw_excluded_names_file: str | None = None


@dataclass(frozen=True)
class PathsConfig:
    runs_dir: str = "runs"
    results_dir: str = "results"


# --------------------------------------------------------------------------- #
# Root
# --------------------------------------------------------------------------- #

# Fields that may legitimately stay ``null`` in a run-ready configuration.
_OPTIONAL_NULLS = frozenset(
    {
        "model.init_weights_source",
        "model.init_weights_sha256",
        "evaluation.lfw_excluded_names_file",
    }
)


@dataclass(frozen=True)
class ExperimentConfig:
    status: str = "planning_only"
    project: str = "aiaa2290-Mini-Ever"
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    sisa: SisaConfig = field(default_factory=SisaConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    canary: CanaryConfig = field(default_factory=CanaryConfig)
    distill: DistillConfig = field(default_factory=DistillConfig)
    unlearning: UnlearningConfig = field(default_factory=UnlearningConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)

    # -- inspection ---------------------------------------------------------- #

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def hash(self) -> str:
        """Stable SHA-256 of the full configuration (used in run records and cache keys)."""
        return sha256_json(self.to_dict())

    def missing_fields(self) -> list[str]:
        """Dotted names of fields that are still ``null`` / empty and must be decided."""
        missing: list[str] = []
        _collect_missing(self.to_dict(), "", missing)
        return [name for name in missing if name not in _OPTIONAL_NULLS]

    def require_complete(self) -> None:
        """Raise if any research decision is still open (see module docstring)."""
        missing = self.missing_fields()
        if missing:
            raise ConfigIncompleteError(
                "These fields must be fixed before a run (see docs/protocol.md): "
                + ", ".join(missing)
            )

    def validate(self) -> None:
        """Check internal consistency. Raises ``ValueError`` on the first problem."""
        pools = self.data.identity_pools
        _check(abs(pools.public + pools.user - 1.0) < 1e-6, "identity_pools must sum to 1")
        r = self.data.split_ratios
        _check(abs(r.train + r.gallery + r.test - 1.0) < 1e-6, "split_ratios must sum to 1")
        _check(0.0 < self.data.accounts.self_share <= 1.0, "accounts.self_share must be in (0, 1]")
        _check(self.data.forget_pool == "user", "only the user pool can be forgotten")
        _check(
            set(self.data.forget_units) <= {"account", "person"},
            "forget_units must be a subset of {'account', 'person'}",
        )
        _check(
            self.model.initialization in {"imagenet_pretrained", "random"},
            "model.initialization must be 'imagenet_pretrained' or 'random' "
            "(face-pretrained weights are forbidden, see Experiment 0)",
        )
        _check(self.model.forbid_face_pretrained_weights, "forbid_face_pretrained_weights must stay true")
        _check(all(0.0 <= r <= 1.0 for r in self.evaluation.trace_miss_rates), "trace_miss_rates in [0, 1]")
        _check(set(self.evaluation.quantization_bits) <= {4, 8}, "quantization_bits must be 4 and/or 8")
        _check(self.sisa.partition_unit == "identity", "SISA shards must be partitioned by identity")


class ConfigIncompleteError(RuntimeError):
    """Raised when a run is attempted while research decisions are still ``null``."""


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def load_config(path: str | Path) -> ExperimentConfig:
    """Read a JSON config file into an :class:`ExperimentConfig` and validate it."""
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)
    config = from_dict(ExperimentConfig, raw)
    config.validate()
    return config


def from_dict(cls: type, data: dict[str, Any]) -> Any:
    """Recursively build dataclass ``cls`` from a plain dict, rejecting unknown keys."""
    if not isinstance(data, dict):
        raise TypeError(f"{cls.__name__} expects an object, got {type(data).__name__}")
    hints = typing.get_type_hints(cls)
    known = {f.name for f in dataclasses.fields(cls)}
    unknown = set(data) - known
    if unknown:
        raise KeyError(f"Unknown key(s) for {cls.__name__}: {sorted(unknown)}")
    kwargs = {name: _coerce(hints[name], value) for name, value in data.items()}
    return cls(**kwargs)


def _coerce(hint: Any, value: Any) -> Any:
    if value is None:
        return None
    if dataclasses.is_dataclass(hint):
        return from_dict(hint, value)
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)
    if origin is typing.Union or origin is types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        return _coerce(non_none[0], value) if len(non_none) == 1 else value
    if origin is tuple:
        return tuple(value)
    return value


def _collect_missing(node: dict[str, Any], prefix: str, out: list[str]) -> None:
    for key, value in node.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            _collect_missing(value, name + ".", out)
        elif value is None or (isinstance(value, (list, tuple)) and not value):
            out.append(name)


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
