"""Experiment 4 - is the whole claim only as strong as its weakest link?

Four system configurations after a deletion request for one forget group:

| config | main model              | gallery           | student                 | deployment |
|--------|-------------------------|-------------------|-------------------------|------------|
| A      | unchanged               | unchanged         | unchanged               | unchanged  |
| B      | exact retrain           | unchanged (stale) | unchanged (stale)       | from new   |
| C      | approximate unlearning  | person removed    | re-distilled from new   | from new   |
| D      | exact retrain           | person removed    | re-distilled from new   | from new   |

Each node is compared with the same node of the reference system (never saw
the group). End-to-end leakage = max over nodes (see
:mod:`mini_ever.evaluation.leakage`); the mean is reported for comparison.

Part 4b: configuration D with incomplete tracing. A fraction ``r`` of the
group's training photos is "missed" (stays in the training set) before exact
retraining; the curve r -> end-to-end leakage tests how much a small T gap
costs. Missed photos are nested across r (see :mod:`mini_ever.data.deletion`).
Leakage is measured on new audit photos, never on the missed photos.

A stale gallery is queried with the model that built it: an attacker holding
an old gallery also holds (or can rebuild) its encoder.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from torch import nn

from mini_ever.context import Context
from mini_ever.data.deletion import PERSON, DeletionRequest, person_removed
from mini_ever.evaluation import scores as S
from mini_ever.experiments.common import jsonable, leakage_table, mean_over_seeds, select_groups, select_seeds
from mini_ever.experiments.exp03_measurable_forgetting import apply_method
from mini_ever.models.gallery import Gallery
from mini_ever.models.quantize import quantize_model

NAME = "exp04_weakest_link"


def _system_scores(
    ctx: Context,
    ids: Sequence[int],
    seed: int,
    main: nn.Module,
    gallery: Gallery,
    gallery_query: nn.Module,
    student: nn.Module,
) -> dict[str, dict[int, float]]:
    deployment, _ = quantize_model(main, 8 if 8 in ctx.config.evaluation.quantization_bits else 4)
    return {
        "gallery": S.gallery_scores(ctx, gallery_query, gallery, ids),
        "main": S.prototype_scores(ctx, main, ids),
        "student": S.prototype_scores(ctx, student, ids),
        "deployment": S.prototype_scores(ctx, deployment, ids),
    }


def _configurations(ctx: Context, ids: Sequence[int], seed: int, approx: str) -> dict[str, dict[str, dict[int, float]]]:
    main = ctx.main_model(seed)
    removed = person_removed(ctx.manifest, ids)
    retrained = ctx.stage2(removed, seed, kind="unlearned")
    approximate, _ = apply_method(ctx, approx, ids, seed)
    old_gallery = ctx.gallery(main)
    old_student = ctx.student(main, seed)
    return {
        "A": _system_scores(ctx, ids, seed, main, old_gallery, main, old_student),
        "B": _system_scores(ctx, ids, seed, retrained, old_gallery, main, old_student),
        "C": _system_scores(
            ctx, ids, seed, approximate.model, ctx.gallery(approximate.model, exclude=ids),
            approximate.model, ctx.student(approximate.model, seed),
        ),
        "D": _system_scores(
            ctx, ids, seed, retrained, ctx.gallery(retrained, exclude=ids), retrained, ctx.student(retrained, seed)
        ),
    }


def _reference_system(ctx: Context, ids: Sequence[int], seed: int) -> dict[str, dict[int, float]]:
    ref = ctx.person_reference(ids, seed)
    return _system_scores(ctx, ids, seed, ref, ctx.gallery(ref, exclude=ids), ref, ctx.student(ref, seed))


def _trace_miss(ctx: Context, ids: Sequence[int], seed: int, rate: float) -> dict[str, dict[int, float]]:
    request = DeletionRequest(tuple(ids), PERSON, rate, ctx.config.evaluation.trace_miss_seed)
    model = ctx.stage2(request.removed_image_ids(ctx.manifest), seed, kind="unlearned")
    return _system_scores(ctx, ids, seed, model, ctx.gallery(model, exclude=ids), model, ctx.student(model, seed))


def _summarise(ctx: Context, systems: list[dict[str, dict[int, float]]], refs: list[dict[str, dict[int, float]]], salt: str):
    nodes = {
        node: (mean_over_seeds(s[node] for s in systems), mean_over_seeds(r[node] for r in refs))
        for node in systems[0]
    }
    per_node, e2e = leakage_table(ctx, nodes, salt)
    return {"nodes": per_node, "end_to_end": e2e}


def run(
    ctx: Context,
    groups: Sequence[int] | None = None,
    seeds: Sequence[int] | None = None,
    approximate_method: str = "neggrad_plus",
    **_: Any,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "experiment": NAME,
        "approximate_method": approximate_method,
        "trace_miss_rates": list(ctx.config.evaluation.trace_miss_rates),
        "groups": {},
    }
    for g in select_groups(ctx, groups):
        ids = ctx.manifest.forget_groups[g]
        seed_list = select_seeds(ctx, seeds)
        refs = [_reference_system(ctx, ids, s) for s in seed_list]
        configs = [_configurations(ctx, ids, s, approximate_method) for s in seed_list]

        group_out: dict[str, Any] = {"configurations": {}, "trace_miss": {}}
        for name in ("A", "B", "C", "D"):
            group_out["configurations"][name] = _summarise(ctx, [c[name] for c in configs], refs, f"{NAME}-g{g}-{name}")
        for rate in ctx.config.evaluation.trace_miss_rates:
            systems = [_trace_miss(ctx, ids, s, rate) for s in seed_list]
            group_out["trace_miss"][f"{rate:g}"] = _summarise(ctx, systems, refs, f"{NAME}-g{g}-r{rate:g}")
        out["groups"][f"group_{g}"] = group_out

    ctx.save_result(NAME, out)
    return jsonable(out)
