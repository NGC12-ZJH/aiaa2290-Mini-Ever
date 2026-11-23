"""Experiment 0 - did the starting models already know these people?

Run before any user-pool training. Two starting points are checked:

* ``imagenet_init`` - pooled ImageNet features, no face training at all;
* ``public_base``   - stage 1, trained on the public pool only.

For each, and each forget group, the forget group is compared with the other
user-pool identities on two metrics (TAR at a fixed FAR, and 1:N top-1 within
the user pool). Both groups are unseen, so the expected verdict is ``pass``
(equivalent within the pre-registered margin).

Positive control: under ``public_base``, public identities (seen in stage 1)
are compared with user identities (unseen). A clear difference proves the
measurement can detect "seen"; if it cannot, the test lacks sensitivity and
the measurement must be improved before trusting the other verdicts.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from torch import nn

from mini_ever.context import Context
from mini_ever.evaluation import scores as S
from mini_ever.evaluation.stats import Verdict, equivalence_verdict, mean_difference
from mini_ever.experiments.common import jsonable, rng, select_groups

NAME = "exp00_prior_familiarity"


def _metrics(ctx: Context, model: nn.Module, identities: Sequence[int]) -> dict[str, dict[int, float]]:
    """Both metrics, computed within ``identities`` only."""
    others = set(ctx.manifest.all_identities) - set(identities)
    gallery = ctx.gallery(model, exclude=others)
    far = ctx.config.evaluation.far_target
    return {
        "verification_tar_at_far": S.tar_at_far(ctx, model, identities, far),
        "retrieval_top1": S.retrieval_top1(ctx, model, gallery, identities),
    }


def run(ctx: Context, groups: Sequence[int] | None = None, **_: Any) -> dict[str, Any]:
    check = ctx.config.evaluation.prior_familiarity_check
    margin = float(check.equivalence_margin)  # type: ignore[arg-type]
    conf = float(ctx.config.evaluation.confidence_level)  # type: ignore[arg-type]
    n_boot = ctx.config.evaluation.bootstrap_samples
    users = list(ctx.manifest.user_identities)
    public = list(ctx.manifest.public_identities)

    starting_points: dict[str, nn.Module] = {}
    if "imagenet_init" in check.models:
        starting_points["imagenet_init"] = ctx.imagenet_init()
    if "public_base" in check.models:
        starting_points["public_base"] = ctx.public_base()

    results: dict[str, Any] = {"forget_vs_other_user": {}, "positive_control": {}}
    for model_name, model in starting_points.items():
        user_metrics = _metrics(ctx, model, users)
        for g in select_groups(ctx, groups):
            forget = set(ctx.manifest.forget_groups[g])
            for metric, values in user_metrics.items():
                a = {i: v for i, v in values.items() if i in forget}
                b = {i: v for i, v in values.items() if i not in forget}
                estimate = mean_difference(a, b, n_boot, conf, rng(ctx, NAME, model_name, g, metric), paired=False)
                results["forget_vs_other_user"].setdefault(model_name, {}).setdefault(f"group_{g}", {})[metric] = {
                    "forget_mean": sum(a.values()) / len(a),
                    "other_mean": sum(b.values()) / len(b),
                    "difference": estimate.as_dict(),
                    "verdict": equivalence_verdict(estimate, margin),
                }

    if "public_base" in starting_points and "public_vs_user_positive_control" in check.comparisons:
        model = starting_points["public_base"]
        both = _metrics(ctx, model, public + users)
        for metric, values in both.items():
            a = {i: values[i] for i in public}
            b = {i: values[i] for i in users}
            estimate = mean_difference(a, b, n_boot, conf, rng(ctx, NAME, "positive", metric), paired=False)
            detected = estimate.low > margin
            results["positive_control"][metric] = {
                "public_mean": sum(a.values()) / len(a),
                "user_mean": sum(b.values()) / len(b),
                "difference": estimate.as_dict(),
                "sensitivity": "detected" if detected else "not detected - improve the measurement first",
                "verdict": Verdict.PASS if detected else Verdict.UNCERTAIN,
            }

    payload = {"experiment": NAME, "margin": margin, "results": results}
    ctx.save_result(NAME, payload)
    return jsonable(payload)
