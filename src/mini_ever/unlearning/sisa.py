"""SISA: Sharded, Isolated, Sliced, Aggregated training (Bourtoule et al., S&P 2021).

The user pool is split into ``S`` shards *by identity* (all photos of a person,
whoever uploaded them, live in one shard). Each shard trains its own model from
the shared public base. A deletion request only retrains the shard that holds
the person, so its cost is roughly ``1/S`` of a full retrain - at the price of
each shard seeing only ``1/S`` of the users.

Aggregation
-----------
* Embeddings: the L2-normalised shard embeddings are concatenated and scaled
  by ``1/sqrt(S)``, so the result is again unit-length (config
  ``embedding_aggregation = concatenate_normalized``). Averaging is not used by
  default because different shard models do not share an embedding space.
* Classification (L1): each shard's softmax is placed into the global label
  space and averaged over the shards that know each class.

Slicing (incremental checkpoints inside a shard) is not implemented; the
config flag ``sisa.slicing_enabled`` must stay ``false``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from mini_ever.context import Context
from mini_ever.data.deletion import person_removed
from mini_ever.data.splits import PUBLIC, TRAIN, ImageRecord, LabelSpace
from mini_ever.models.face_model import FaceModel, with_new_head
from mini_ever.training.trainer import train_loop
from mini_ever.unlearning.base import UnlearningOutput
from mini_ever.utils.hashing import sha256_strings
from mini_ever.utils.seeding import derive_rng, derive_seed


def assign_shards(identities: Iterable[int], n_shards: int, seed: int) -> dict[int, int]:
    """Random, balanced identity -> shard assignment."""
    ordered = derive_rng(seed, "shards", n_shards).permutation(sorted(identities))
    return {int(identity): position % n_shards for position, identity in enumerate(ordered)}


class ShardedFaceModel(nn.Module):
    def __init__(self, shards: Sequence[FaceModel], global_labels: Sequence[int]) -> None:
        super().__init__()
        self.shards = nn.ModuleList(shards)
        self.register_buffer("label_ids", torch.as_tensor(list(global_labels), dtype=torch.long))
        position = {identity: i for i, identity in enumerate(global_labels)}
        for k, shard in enumerate(shards):
            index = torch.as_tensor([position[int(i)] for i in shard.label_ids.tolist()], dtype=torch.long)
            self.register_buffer(f"_index_{k}", index)

    @property
    def embedding_dim(self) -> int:
        return sum(shard.embedding_dim for shard in self.shards)

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        parts = [F.normalize(shard.backbone(x), dim=1) for shard in self.shards]
        return torch.cat(parts, dim=1) / len(parts) ** 0.5

    def predict_identity(self, x: torch.Tensor) -> torch.Tensor:
        total = torch.zeros(x.shape[0], len(self.label_ids), device=x.device)
        count = torch.zeros(len(self.label_ids), device=x.device)
        for k, shard in enumerate(self.shards):
            index = getattr(self, f"_index_{k}")
            total[:, index] += F.softmax(shard.logits(x), dim=1)
            count[index] += 1
        mean = total / count.clamp(min=1)
        mean[:, count == 0] = -1.0
        return self.label_ids[mean.argmax(dim=1)]


def shard_records(
    ctx: Context, shard: int, shard_of: dict[int, int], removed: frozenset[str]
) -> list[ImageRecord]:
    include_public = bool(ctx.config.sisa.include_public_pool_in_shards)
    return [
        r
        for r in ctx.manifest.select(role=TRAIN)
        if r.image_id not in removed
        and ((r.pool == PUBLIC and include_public) or (r.pool != PUBLIC and shard_of.get(r.identity) == shard))
    ]


def shard_labels(ctx: Context, shard: int, shard_of: dict[int, int]) -> LabelSpace:
    users = [i for i, s in shard_of.items() if s == shard]
    public = list(ctx.manifest.public_identities) if ctx.config.sisa.include_public_pool_in_shards else []
    return LabelSpace(tuple(sorted(public + users)))


def train_shard(
    ctx: Context,
    shard: int,
    shard_of: dict[int, int],
    removed: frozenset[str],
    seed: int,
    backbone: str,
) -> FaceModel:
    """One shard model (cached on its own data, so untouched shards are reused)."""
    records = shard_records(ctx, shard, shard_of, removed)
    labels = shard_labels(ctx, shard, shard_of)
    base = ctx.public_base(backbone)
    shard_removed = frozenset(r for r in removed if shard_of.get(ctx.manifest.by_image_id[r].identity) == shard)
    shard_seed = derive_seed(seed, "shard", len(set(shard_of.values())), shard)
    return ctx.cached_model(  # type: ignore[return-value]
        "shard",
        {
            "backbone": backbone,
            "seed": shard_seed,
            "shard": shard,
            "assignment": sha256_strings(f"{i}:{s}" for i, s in shard_of.items()),
            "removed": sha256_strings(shard_removed),
            "include_public": ctx.config.sisa.include_public_pool_in_shards,
        },
        factory=lambda: with_new_head(base, ctx.config.model, labels.identities),
        train=lambda m: train_loop(m, ctx.train_dataset(records, labels), ctx.stage_spec(2), ctx.device, shard_seed),
        register=ctx.register_trained("shard", records, (ctx.artifact_id(base) or "",)),
    )


def build_sharded(
    ctx: Context,
    n_shards: int,
    removed: frozenset[str],
    seed: int,
    backbone: str | None = None,
    assignment_seed: int | None = None,
) -> tuple[ShardedFaceModel, dict[int, int]]:
    """Train (or load) all shards. ``assignment_seed`` defaults to ``seed``; a
    reference passes the evaluated model's seed so both use the *same* shards
    (protocol: "SISA 的参照沿用相同分片方案")."""
    backbone = backbone or ctx.config.sisa.backbone
    assignment_seed = seed if assignment_seed is None else assignment_seed
    shard_of = assign_shards(ctx.manifest.user_identities, n_shards, derive_seed(assignment_seed, "assignment"))
    shards = [train_shard(ctx, k, shard_of, removed, seed, backbone) for k in range(n_shards)]
    model = ShardedFaceModel(shards, ctx.labels2.identities).to(ctx.device).eval()
    shard_ids = [ctx.artifact_id(s) or "" for s in shards]
    ctx.adopt(model, f"sharded-S{n_shards}-{sha256_strings(shard_ids)[:16]}", "main", shard_ids, notes="SISA ensemble")
    return model, shard_of


def affected_shards(shard_of: dict[int, int], identities: Iterable[int]) -> list[int]:
    return sorted({shard_of[i] for i in identities})


def sisa_unlearn(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    """Exact SISA deletion: retrain only the shards that hold the forgotten people.

    ``model`` is ignored - SISA is its own training design and is never
    converted from a monolithic checkpoint (README, 实验 3).
    """
    n_shards = ctx.config.sisa.shard_counts[0]
    _, shard_of = build_sharded(ctx, n_shards, frozenset(), seed)
    touched = affected_shards(shard_of, identities)
    updated, _ = build_sharded(ctx, n_shards, removed, seed)
    seconds = float(np.sum([ctx.train_seconds(updated.shards[k]) for k in touched]))
    return UnlearningOutput(updated, "sisa", seconds, exact=True, notes=f"S={n_shards}, retrained shards {len(touched)}")


def sisa_reference(ctx: Context, identities: Iterable[int], seed: int) -> ShardedFaceModel:
    """Matched reference: same sharding design, never trained on the forgotten people."""
    removed = person_removed(ctx.manifest, identities)
    model, _ = build_sharded(
        ctx, ctx.config.sisa.shard_counts[0], removed, ctx.reference_seed(seed), assignment_seed=seed
    )
    return model
