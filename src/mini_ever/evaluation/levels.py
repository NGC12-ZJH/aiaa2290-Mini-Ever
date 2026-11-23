"""The five test levels L1-L5 (README, 实验 3).

| Level | Question                                   | Compared with the reference via       |
|-------|--------------------------------------------|----------------------------------------|
| L1    | Does the classifier still name the person? | accuracy difference, equivalence test  |
| L2    | Can a membership attack tell?              | U-LiRA AUC (or exploratory advantage)  |
| L3    | Do L1/L2 change after INT8 / INT4?         | same tests on quantised copies         |
| L4    | Does the person come back after relearning?| relearning-curve area difference       |
| L5    | Does the planted canary still fire?        | trigger-rate difference                |

Each level returns a :class:`LevelResult` with a four-state verdict. Margins
come from ``evaluation.equivalence_margins`` and must be fixed before a run:
keys ``l1``, ``l2``, ``l4``, ``l5`` and ``leakage``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from torch import nn

from mini_ever.context import Context
from mini_ever.data.deletion import person_removed
from mini_ever.evaluation import scores as S
from mini_ever.evaluation.mia import ulira
from mini_ever.evaluation.relearn import relearn_curve
from mini_ever.evaluation.stats import (
    Estimate,
    Verdict,
    advantage_estimate,
    equivalence_verdict,
    mean_difference,
    upper_bound_verdict,
)
from mini_ever.models.quantize import quantize_model


@dataclass(frozen=True)
class LevelResult:
    level: str
    metric: str
    method_value: float | None
    reference_value: float | None
    estimate: Estimate | None
    verdict: Verdict
    exploratory: bool = False
    note: str = ""


def not_applicable(level: str, metric: str, note: str) -> LevelResult:
    return LevelResult(level, metric, None, None, None, Verdict.NOT_APPLICABLE, note=note)


class LevelEvaluator:
    """Runs L1-L5 for one forget group, comparing a model with its reference."""

    def __init__(self, ctx: Context, group_index: int, rng: np.random.Generator) -> None:
        self.ctx = ctx
        self.group_index = group_index
        self.identities = ctx.manifest.forget_groups[group_index]
        self.rng = rng
        ev = ctx.config.evaluation
        self.margins = dict(ev.equivalence_margins or {})
        self.n_boot = ev.bootstrap_samples
        self.confidence = float(ev.confidence_level)  # type: ignore[arg-type]

    def _margin(self, key: str) -> float:
        if key not in self.margins:
            raise KeyError(f"evaluation.equivalence_margins needs a value for {key!r}")
        return float(self.margins[key])

    def _diff(self, level: str, metric: str, a: dict[int, float], b: dict[int, float], margin_key: str) -> LevelResult:
        estimate = mean_difference(a, b, self.n_boot, self.confidence, self.rng, paired=True)
        return LevelResult(
            level,
            metric,
            float(np.mean(list(a.values()))),
            float(np.mean(list(b.values()))),
            estimate,
            equivalence_verdict(estimate, self._margin(margin_key)),
        )

    # -- L1 ------------------------------------------------------------------ #

    def l1(self, model: nn.Module, reference: nn.Module, level: str = "L1") -> LevelResult:
        a = S.classifier_accuracy(self.ctx, model, self.identities)
        b = S.classifier_accuracy(self.ctx, reference, self.identities)
        return self._diff(level, "classifier_accuracy_on_audit_photos", a, b, "l1")

    # -- L2 ------------------------------------------------------------------ #

    def l2_exploratory(self, model: nn.Module, reference: nn.Module, level: str = "L2") -> LevelResult:
        """Prototype-score advantage over identities. A simplified baseline, not U-LiRA."""
        a = S.prototype_scores(self.ctx, model, self.identities)
        b = S.prototype_scores(self.ctx, reference, self.identities)
        estimate = advantage_estimate(a, b, self.n_boot, self.confidence, self.rng)
        return LevelResult(
            level,
            "prototype_score_advantage",
            float(np.mean(list(a.values()))),
            float(np.mean(list(b.values()))),
            estimate,
            upper_bound_verdict(estimate, self._margin("leakage")),
            exploratory=True,
            note="simplified baseline, not U-LiRA",
        )

    def l2_ulira(self, unlearned_shadows: Sequence[nn.Module], retrained_shadows: Sequence[nn.Module]) -> LevelResult:
        """U-LiRA over the forgotten training photos (see :mod:`.mia`)."""
        records = [self.ctx.manifest.by_image_id[i] for i in sorted(person_removed(self.ctx.manifest, self.identities))]
        u = np.stack([S.example_scores(self.ctx, m, records) for m in unlearned_shadows])
        r = np.stack([S.example_scores(self.ctx, m, records) for m in retrained_shadows])
        result = ulira(u, r)
        if result is None:
            return not_applicable("L2", "ulira_auc", "needs >= 3 shadow models of each kind")
        columns = np.arange(u.shape[1])
        draws = []
        for _ in range(self.n_boot):
            pick = self.rng.choice(columns, len(columns))
            draw = ulira(u[:, pick], r[:, pick])
            draws.append(draw.auc - 0.5 if draw else np.nan)
        alpha = (1 - self.confidence) / 2
        low, high = np.nanquantile(draws, [alpha, 1 - alpha])
        estimate = Estimate(result.auc - 0.5, float(low), float(high), u.shape[1], self.confidence)
        return LevelResult(
            "L2",
            "ulira_auc_minus_0.5",
            result.auc,
            0.5,
            estimate,
            equivalence_verdict(estimate, self._margin("l2")),
            note=f"{result.note}; accuracy={result.accuracy:.3f}; examples resampled (not identities)",
        )

    # -- L3 ------------------------------------------------------------------ #

    def l3(self, model: nn.Module, reference: nn.Module) -> list[LevelResult]:
        results: list[LevelResult] = []
        for bits in self.ctx.config.evaluation.quantization_bits:
            q_model, _ = quantize_model(model, bits)
            q_reference, _ = quantize_model(reference, bits)
            results.append(self.l1(q_model, q_reference, level=f"L3-INT{bits}/L1"))
            results.append(self.l2_exploratory(q_model, q_reference, level=f"L3-INT{bits}/L2"))
        return results

    # -- L4 ------------------------------------------------------------------ #

    def l4(self, model: nn.Module, reference: nn.Module, seed: int) -> LevelResult:
        if not hasattr(model, "logits"):
            return not_applicable("L4", "relearn_curve_area", "relearning a sharded ensemble is not defined here")
        a = relearn_curve(self.ctx, model, self.identities, seed).area()
        b = relearn_curve(self.ctx, reference, self.identities, seed).area()
        return self._diff("L4", "relearn_curve_area", a, b, "l4")

    # -- L5 ------------------------------------------------------------------ #

    def l5(self, model: nn.Module, reference: nn.Module) -> LevelResult:
        canary = self.ctx.canary
        if canary is None:
            return not_applicable("L5", "trigger_rate", "canaries disabled")
        trigger, target = canary.triggers[self.group_index], canary.target_identities[self.group_index]
        a = S.trigger_rates(self.ctx, model, self.identities, trigger, target)
        b = S.trigger_rates(self.ctx, reference, self.identities, trigger, target)
        return self._diff("L5", "trigger_rate", a, b, "l5")
