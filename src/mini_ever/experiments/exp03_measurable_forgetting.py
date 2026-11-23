"""Experiment 3 (M) - six methods x five test levels.

For each forget group and seed, every method removes the group's photos and the
result is compared with its matched reference at L1-L5 (see
:mod:`mini_ever.evaluation.levels`). Approximate methods start from the main
model; full retraining is its own run; SISA uses its own sharded design and its
own matched reference (never converted from the monolithic checkpoint).

L2 uses U-LiRA when ``evaluation.shadow_model_count >= 3``; each shadow pair is
(a) the method applied to a main model trained with a shadow seed and (b) a
model retrained without the forget group with another shadow seed. Otherwise
L2 falls back to the exploratory prototype-score baseline, labelled as such.

Every method also reports its update cost and utility on remaining users / LFW.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from torch import nn

from mini_ever.context import Context
from mini_ever.data.deletion import person_removed
from mini_ever.evaluation.levels import LevelEvaluator
from mini_ever.evaluation.mia import MIN_SHADOWS
from mini_ever.evaluation.utility import utility_report
from mini_ever.experiments.common import jsonable, rng, select_groups, select_seeds
from mini_ever.unlearning import METHODS, sisa_reference
from mini_ever.unlearning.base import UnlearningOutput
from mini_ever.utils.hashing import sha256_json
from mini_ever.utils.seeding import derive_seed

NAME = "exp03_measurable_forgetting"


def apply_method(ctx: Context, name: str, ids: Sequence[int], seed: int) -> tuple[UnlearningOutput, nn.Module]:
    """Run one method for one seed; returns (output, matched reference)."""
    removed = person_removed(ctx.manifest, ids)
    main = ctx.main_model(seed)
    output = METHODS[name](ctx, main, removed, ids, seed)
    reference = sisa_reference(ctx, ids, seed) if name == "sisa" else ctx.person_reference(ids, seed)
    if ctx.artifact_id(output.model) is None:
        tag = sha256_json([name, ctx.artifact_id(main), sorted(ids), seed])[:16]
        ctx.adopt(output.model, f"unlearned-{name}-{tag}", "unlearned", (ctx.artifact_id(main) or "",), notes=name)
    return output, reference


def _shadows(ctx: Context, name: str, ids: Sequence[int], seed: int) -> tuple[list[nn.Module], list[nn.Module]] | None:
    count = ctx.config.evaluation.shadow_model_count or 0
    if count < MIN_SHADOWS:
        return None
    removed = person_removed(ctx.manifest, ids)
    unlearned, retrained = [], []
    for k in range(count):
        shadow_seed = derive_seed(seed, "shadow", k)
        output, _ = apply_method(ctx, name, ids, shadow_seed)
        unlearned.append(output.model)
        retrained.append(ctx.stage2(removed, derive_seed(shadow_seed, "retrained"), kind="reference"))
    return unlearned, retrained


def run(
    ctx: Context,
    groups: Sequence[int] | None = None,
    seeds: Sequence[int] | None = None,
    methods: Sequence[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    methods = list(methods or METHODS)
    unknown = set(methods) - set(METHODS)
    if unknown:
        raise ValueError(f"unknown method(s): {sorted(unknown)}")

    out: dict[str, Any] = {"experiment": NAME, "methods": methods, "runs": []}
    for g in select_groups(ctx, groups):
        ids = ctx.manifest.forget_groups[g]
        for s_index, s in enumerate(select_seeds(ctx, seeds)):
            for name in methods:
                output, reference = apply_method(ctx, name, ids, s)
                levels = LevelEvaluator(ctx, g, rng(ctx, NAME, g, s, name))
                shadows = _shadows(ctx, name, ids, s)
                results = [levels.l1(output.model, reference)]
                results.append(levels.l2_ulira(*shadows) if shadows else levels.l2_exploratory(output.model, reference))
                results += levels.l3(output.model, reference)
                results.append(levels.l4(output.model, reference, derive_seed(s, "relearn")))
                results.append(levels.l5(output.model, reference))
                out["runs"].append(
                    {
                        "group": g,
                        "seed_index": s_index,
                        "method": name,
                        "exact": output.exact,
                        "update_seconds": output.seconds,
                        "notes": output.notes,
                        "levels": results,
                        "utility": utility_report(ctx, output.model, ids),
                    }
                )
    ctx.save_result(NAME, out)
    return jsonable(out)
