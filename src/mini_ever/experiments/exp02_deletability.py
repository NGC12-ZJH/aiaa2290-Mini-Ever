"""Experiment 2 (D) - what does a deletion request cost, by design?

Designs compared (one seed):

* ``monolith``       - the main backbone, S = 1, full stage-2 retrain per request;
* ``sisa-S<k>``      - SISA with ``k`` shards of the SISA backbone, including
  ``k = 1`` as the same-backbone control (README: separates the effect of
  sharding from the ResNet-50 vs ResNet-18 difference).

``sisa.sequential_requests`` deletion requests arrive one by one; deletions
accumulate (a forgotten person never comes back). For every request we record

* the local cost - GPU seconds to retrain the affected model / shard;
* every ``sisa.full_chain_every`` requests, the full-chain cost - local cost
  plus re-distilling the student, rebuilding the gallery and regenerating the
  INT8 deployment copy.

Utility (closed-set top-1 and LFW if available) is reported before and after.

Exactness note: each retrained shard is, by construction, the model that the
same shard would have produced without those people from the start (same
assignment, seed and data), so SISA deletion is exact (protocol, 对照).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mini_ever.context import Context
from mini_ever.data.deletion import person_removed
from mini_ever.evaluation.utility import utility_report
from mini_ever.experiments.common import jsonable
from mini_ever.models.quantize import quantize_model
from mini_ever.unlearning.sisa import affected_shards, build_sharded
from mini_ever.utils.timing import Stopwatch

NAME = "exp02_deletability"


def deletion_queue(ctx: Context, n: int) -> list[int]:
    """The first ``n`` forget-group identities, group by group."""
    queue = [i for group in ctx.manifest.forget_groups for i in group]
    if n > len(queue):
        raise ValueError(f"only {len(queue)} forget identities are available for {n} requests")
    return queue[:n]


def _full_chain(ctx: Context, model, cumulative_ids: list[int], seed: int, local: float) -> dict[str, float]:
    student_seconds = ctx.train_seconds(ctx.student(model, seed))
    with Stopwatch() as gallery_watch:
        ctx.gallery(model, exclude=cumulative_ids)
    with Stopwatch() as quant_watch:
        quantize_model(model, 8)
    return {
        "local": local,
        "student": student_seconds,
        "gallery": gallery_watch.seconds,
        "deployment": quant_watch.seconds,
        "total": local + student_seconds + gallery_watch.seconds + quant_watch.seconds,
    }


def _run_design(ctx: Context, design: str, n_shards: int, backbone: str, seed: int, queue: list[int]) -> dict[str, Any]:
    sisa = ctx.config.sisa

    def build(removed: frozenset[str]):
        if design == "monolith":
            model = ctx.stage2(removed, seed, backbone)
            return model, None
        return build_sharded(ctx, n_shards, removed, seed, backbone)

    model, shard_of = build(frozenset())
    initial = (
        ctx.train_seconds(model)
        if shard_of is None
        else sum(ctx.train_seconds(s) for s in model.shards)  # type: ignore[union-attr]
    )
    record: dict[str, Any] = {
        "design": design,
        "shards": n_shards,
        "backbone": backbone,
        "initial_training_seconds": initial,
        "utility_before": utility_report(ctx, model, ()),
        "requests": [],
    }

    cumulative: set[str] = set()
    forgotten: list[int] = []
    for k, identity in enumerate(queue, start=1):
        cumulative |= person_removed(ctx.manifest, [identity])
        forgotten.append(identity)
        model, shard_of = build(frozenset(cumulative))
        if shard_of is None:
            local = ctx.train_seconds(model)
        else:
            (shard,) = affected_shards(shard_of, [identity])
            local = ctx.train_seconds(model.shards[shard])  # type: ignore[union-attr]
        entry: dict[str, Any] = {"request": k, "local_seconds": local}
        if k % sisa.full_chain_every == 0:
            entry["full_chain_seconds"] = _full_chain(ctx, model, forgotten, seed, local)
        record["requests"].append(entry)

    record["cumulative_local_seconds"] = sum(r["local_seconds"] for r in record["requests"])
    record["utility_after"] = utility_report(ctx, model, forgotten)
    return record


def run(ctx: Context, seeds: Sequence[int] | None = None, **_: Any) -> dict[str, Any]:
    seed = (list(seeds) if seeds else list(ctx.seeds))[0]
    queue = deletion_queue(ctx, ctx.config.sisa.sequential_requests)
    sisa = ctx.config.sisa

    designs = [("monolith", 1, ctx.config.model.backbone)]
    designs += [(f"sisa-S{k}", k, sisa.backbone) for k in sorted({1, *sisa.shard_counts})]
    out = {
        "experiment": NAME,
        "seed_index": 0,
        "requests": len(queue),
        "designs": [_run_design(ctx, name, k, bb, seed, queue) for name, k, bb in designs],
    }
    ctx.save_result(NAME, out)
    return jsonable(out)
