"""Experiment 1 (T) - delete the photos, then look everywhere else.

Part 1: only the original photos of the forget group are deleted from the
photo store; every other artifact is left as it was. Each node is compared
with the matching node of a reference system that never saw these people:

| node        | evaluated system                    | reference system                         |
|-------------|-------------------------------------|------------------------------------------|
| photo store | photo count after deletion          | -                                        |
| gallery     | main-model gallery, still enrolled  | reference gallery, never enrolled        |
| main        | main model                          | person reference model                   |
| student     | student distilled from main         | student distilled from the reference     |
| deployment  | INT8 copy of main                   | INT8 copy of the reference               |
| archive     | pre-deletion checkpoint (= main)    | person reference model                   |

Part 1b: "account deletion" (only the user's own uploads removed, exact
retraining) versus the person reference. A gap here is a *definition* gap:
deleting an account is not forgetting a person, whatever algorithm is used.
The person-reference-vs-person-reference gap across seeds is reported as the
noise floor.

The artifact version manifest lists every registered artifact that contains
the forget group (counts by kind only).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from mini_ever.context import Context
from mini_ever.data.deletion import person_removed
from mini_ever.data.splits import TRAIN
from mini_ever.evaluation import scores as S
from mini_ever.evaluation.stats import advantage_estimate
from mini_ever.experiments.common import jsonable, leakage_table, mean_over_seeds, rng, select_groups, select_seeds
from mini_ever.models.quantize import quantize_model

NAME = "exp01_traceability"


def _deployment_bits(ctx: Context) -> int:
    bits = ctx.config.evaluation.quantization_bits
    return 8 if 8 in bits else bits[0]


def run(
    ctx: Context, groups: Sequence[int] | None = None, seeds: Sequence[int] | None = None, **_: Any
) -> dict[str, Any]:
    bits = _deployment_bits(ctx)
    out: dict[str, Any] = {"experiment": NAME, "deployment_bits": bits, "groups": {}}

    for g in select_groups(ctx, groups):
        ids = ctx.manifest.forget_groups[g]
        removed = person_removed(ctx.manifest, ids)
        node_scores: dict[str, list[tuple[dict, dict]]] = {}
        account_gap: list[tuple[dict, dict]] = []
        person_refs: list[dict] = []

        for s in select_seeds(ctx, seeds):
            main = ctx.main_model(s)
            ref = ctx.person_reference(ids, s)
            ctx.registry.register(f"archive-of-{ctx.artifact_id(main)}", "archive", (), (), (ctx.artifact_id(main) or "",))
            q_main, _ = quantize_model(main, bits)
            q_ref, _ = quantize_model(ref, bits)
            pairs = {
                "gallery": (
                    S.gallery_scores(ctx, main, ctx.gallery(main), ids),
                    S.gallery_scores(ctx, ref, ctx.gallery(ref, exclude=ids), ids),
                ),
                "main": (S.prototype_scores(ctx, main, ids), S.prototype_scores(ctx, ref, ids)),
                "student": (
                    S.prototype_scores(ctx, ctx.student(main, s), ids),
                    S.prototype_scores(ctx, ctx.student(ref, s), ids),
                ),
                "deployment": (S.prototype_scores(ctx, q_main, ids), S.prototype_scores(ctx, q_ref, ids)),
            }
            pairs["archive"] = pairs["main"]  # the archived checkpoint is the untouched main model
            for node, pair in pairs.items():
                node_scores.setdefault(node, []).append(pair)

            account_ref = ctx.account_reference(ids, s)
            person_scores = S.prototype_scores(ctx, ref, ids)
            account_gap.append((S.prototype_scores(ctx, account_ref, ids), person_scores))
            person_refs.append(person_scores)

        averaged = {
            node: (mean_over_seeds(a for a, _ in pairs), mean_over_seeds(b for _, b in pairs))
            for node, pairs in node_scores.items()
        }
        nodes, e2e = leakage_table(ctx, averaged, f"{NAME}-g{g}")

        ev = ctx.config.evaluation
        conf = float(ev.confidence_level)  # type: ignore[arg-type]
        account_estimate = advantage_estimate(
            mean_over_seeds(a for a, _ in account_gap),
            mean_over_seeds(b for _, b in account_gap),
            ev.bootstrap_samples,
            conf,
            rng(ctx, NAME, g, "account"),
        )
        noise = (
            advantage_estimate(person_refs[0], person_refs[1], ev.bootstrap_samples, conf, rng(ctx, NAME, g, "noise"))
            if len(person_refs) >= 2
            else None
        )

        photos_before = len(ctx.manifest.select(role=TRAIN, identities=ids))
        affected = Counter(r.kind for r in ctx.registry.affected_by(ids))
        out["groups"][f"group_{g}"] = {
            "photo_store": {"photos_before": photos_before, "photos_after": photos_before - len(removed)},
            "nodes": nodes,
            "end_to_end": e2e,
            "account_vs_person": {
                "main_model_advantage": account_estimate,
                "noise_floor_reference_vs_reference": noise if noise is not None else "n/a (needs >= 2 seeds)",
            },
            "affected_artifacts_by_kind": dict(affected),
        }

    ctx.save_result(NAME, out)
    return jsonable(out)
