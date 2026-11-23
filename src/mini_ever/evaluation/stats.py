"""Statistics: bootstrap intervals, AUC, attack advantage and four-state verdicts.

Resampling unit
---------------
Photos of the same person are not independent, so every bootstrap here
resamples *identities* (protocol: "避免把同一身份的多张照片当作完全独立重复").
Inputs are therefore ``identity -> value`` dictionaries.

Verdicts
--------
The protocol uses four states: ``pass`` / ``fail`` / ``uncertain`` / ``n/a``.
For an equivalence question ("does the deleted model behave like the
reference?") with pre-registered margin ``m`` and interval ``[low, high]``:

* ``pass``      - the whole interval lies inside ``[-m, m]`` (equivalent);
* ``fail``      - the whole interval lies outside it (clearly different);
* ``uncertain`` - anything else. *Not rejecting a difference is not proof of
  equivalence*, so a wide interval is ``uncertain``, never ``pass``.
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np


class Verdict(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"
    NOT_APPLICABLE = "n/a"


@dataclass(frozen=True)
class Estimate:
    """A point estimate with a bootstrap interval over ``n`` identities."""

    value: float
    low: float
    high: float
    n: int
    confidence: float

    def as_dict(self) -> dict[str, float]:
        return {"value": self.value, "low": self.low, "high": self.high, "n": self.n, "confidence": self.confidence}


def auc(positive: np.ndarray, negative: np.ndarray) -> float:
    """P(score_pos > score_neg) + 0.5 * P(tie)  (Mann-Whitney AUC)."""
    positive, negative = np.asarray(positive, float), np.asarray(negative, float)
    if len(positive) == 0 or len(negative) == 0:
        return float("nan")
    combined = np.concatenate([positive, negative])
    order = combined.argsort(kind="mergesort")
    ranks = np.empty(len(combined))
    sorted_values = combined[order]
    # average ranks for ties
    start = 0
    while start < len(combined):
        end = start
        while end + 1 < len(combined) and sorted_values[end + 1] == sorted_values[start]:
            end += 1
        ranks[order[start : end + 1]] = 0.5 * (start + end) + 1.0
        start = end + 1
    rank_sum = ranks[: len(positive)].sum()
    return float((rank_sum - len(positive) * (len(positive) + 1) / 2) / (len(positive) * len(negative)))


def advantage(node_scores: np.ndarray, reference_scores: np.ndarray) -> float:
    """Distinguishing advantage in [0, 1]: ``max(0, 2 * AUC - 1)``.

    0 means the node's scores look exactly like the reference's (no evidence of
    remaining influence); 1 means every node score exceeds every reference score.
    Only the direction "node remembers *more* than the reference" counts.
    """
    value = auc(node_scores, reference_scores)
    return 0.0 if np.isnan(value) else max(0.0, 2.0 * value - 1.0)


def bootstrap(
    statistic: Callable[[np.ndarray], float],
    keys: np.ndarray,
    n_boot: int,
    confidence: float,
    rng: np.random.Generator,
) -> Estimate:
    """Percentile bootstrap of ``statistic(resampled_keys)``."""
    keys = np.asarray(keys)
    value = float(statistic(keys))
    draws = np.array([statistic(rng.choice(keys, size=len(keys), replace=True)) for _ in range(n_boot)])
    draws = draws[~np.isnan(draws)]
    alpha = (1.0 - confidence) / 2.0
    low, high = (np.quantile(draws, [alpha, 1.0 - alpha]) if len(draws) else (np.nan, np.nan))
    return Estimate(value, float(low), float(high), len(keys), confidence)


def mean_difference(
    a: Mapping[int, float],
    b: Mapping[int, float],
    n_boot: int,
    confidence: float,
    rng: np.random.Generator,
    paired: bool = True,
) -> Estimate:
    """``mean(a) - mean(b)`` with identities resampled.

    ``paired=True`` (same identities in both, e.g. node vs reference) resamples
    identities jointly; otherwise each group is resampled on its own.
    """
    if paired:
        keys = np.asarray(sorted(set(a) & set(b)))
        diffs = {k: a[k] - b[k] for k in keys}
        return bootstrap(lambda ks: float(np.mean([diffs[k] for k in ks])), keys, n_boot, confidence, rng)

    keys_a, keys_b = np.asarray(sorted(a)), np.asarray(sorted(b))
    value = float(np.mean([a[k] for k in keys_a]) - np.mean([b[k] for k in keys_b]))
    draws = [
        np.mean([a[k] for k in rng.choice(keys_a, len(keys_a))]) - np.mean([b[k] for k in rng.choice(keys_b, len(keys_b))])
        for _ in range(n_boot)
    ]
    alpha = (1.0 - confidence) / 2.0
    low, high = np.quantile(draws, [alpha, 1.0 - alpha])
    return Estimate(value, float(low), float(high), len(keys_a) + len(keys_b), confidence)


def advantage_estimate(
    node: Mapping[int, float],
    reference: Mapping[int, float],
    n_boot: int,
    confidence: float,
    rng: np.random.Generator,
) -> Estimate:
    """:func:`advantage` over identities, with a paired identity bootstrap."""
    keys = np.asarray(sorted(set(node) & set(reference)))

    def stat(ks: np.ndarray) -> float:
        return advantage(np.array([node[k] for k in ks]), np.array([reference[k] for k in ks]))

    return bootstrap(stat, keys, n_boot, confidence, rng)


def equivalence_verdict(estimate: Estimate | None, margin: float) -> Verdict:
    """Two-sided equivalence check against ``[-margin, margin]`` (see module docstring)."""
    if estimate is None or np.isnan(estimate.low) or np.isnan(estimate.high):
        return Verdict.NOT_APPLICABLE
    if -margin <= estimate.low and estimate.high <= margin:
        return Verdict.PASS
    if estimate.low > margin or estimate.high < -margin:
        return Verdict.FAIL
    return Verdict.UNCERTAIN


def upper_bound_verdict(estimate: Estimate | None, margin: float) -> Verdict:
    """For one-sided quantities such as advantage (>= 0): pass if high <= margin,
    fail if low > margin, otherwise uncertain."""
    if estimate is None or np.isnan(estimate.low) or np.isnan(estimate.high):
        return Verdict.NOT_APPLICABLE
    if estimate.high <= margin:
        return Verdict.PASS
    if estimate.low > margin:
        return Verdict.FAIL
    return Verdict.UNCERTAIN
