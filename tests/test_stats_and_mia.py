import numpy as np
import pytest

from mini_ever.evaluation.leakage import end_to_end
from mini_ever.evaluation.mia import ulira
from mini_ever.evaluation.stats import (
    Estimate,
    Verdict,
    advantage,
    advantage_estimate,
    auc,
    equivalence_verdict,
    mean_difference,
    upper_bound_verdict,
)


def test_auc_basic_cases():
    assert auc([3, 4], [1, 2]) == 1.0
    assert auc([1, 2], [3, 4]) == 0.0
    assert auc([1, 1], [1, 1]) == 0.5
    assert auc([1, 3], [2, 4]) == pytest.approx(0.25)


def test_advantage_is_one_sided():
    assert advantage(np.array([5, 6]), np.array([1, 2])) == 1.0
    assert advantage(np.array([1, 2]), np.array([5, 6])) == 0.0


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [(-0.05, 0.05, Verdict.PASS), (0.2, 0.3, Verdict.FAIL), (-0.05, 0.3, Verdict.UNCERTAIN)],
)
def test_equivalence_verdict(low, high, expected):
    assert equivalence_verdict(Estimate(0.0, low, high, 10, 0.9), margin=0.1) is expected


def test_upper_bound_verdict():
    assert upper_bound_verdict(Estimate(0.05, 0.0, 0.1, 10, 0.9), 0.2) is Verdict.PASS
    assert upper_bound_verdict(Estimate(0.5, 0.3, 0.7, 10, 0.9), 0.2) is Verdict.FAIL
    assert upper_bound_verdict(None, 0.2) is Verdict.NOT_APPLICABLE


def test_mean_difference_paired_and_unpaired():
    rng = np.random.default_rng(0)
    a = {i: 1.0 + 0.01 * i for i in range(20)}
    b = {i: 0.0 + 0.01 * i for i in range(20)}
    paired = mean_difference(a, b, 200, 0.9, rng, paired=True)
    assert paired.value == pytest.approx(1.0) and paired.low == pytest.approx(1.0)
    unpaired = mean_difference(a, {i + 100: v for i, v in b.items()}, 200, 0.9, rng, paired=False)
    assert unpaired.low < 1.0 < unpaired.high or unpaired.value == pytest.approx(1.0)


def test_advantage_estimate_resamples_identities():
    rng = np.random.default_rng(1)
    node = {i: float(i) + 10 for i in range(15)}
    ref = {i: float(i) for i in range(15)}
    estimate = advantage_estimate(node, ref, 100, 0.9, rng)
    assert estimate.n == 15 and 0.0 <= estimate.low <= estimate.value <= 1.0


def test_end_to_end_takes_the_weakest_node():
    rng = np.random.default_rng(2)
    same = {i: float(i) for i in range(10)}
    leaky = {i: float(i) + 100 for i in range(10)}
    result = end_to_end({"main": (same, same), "gallery": (leaky, same)}, 0.2, 100, 0.9, rng)
    assert result.weakest_node == "gallery"
    assert result.leakage.value == 1.0 and result.credibility == 0.0
    assert result.mean_leakage == pytest.approx(0.5)


def test_ulira_separable_vs_identical():
    rng = np.random.default_rng(3)
    base = rng.normal(size=(1, 50))
    unlearned = base + 2.0 + rng.normal(scale=0.1, size=(4, 50))
    retrained = base + rng.normal(scale=0.1, size=(4, 50))
    assert ulira(unlearned, retrained).auc > 0.95
    same_u = base + rng.normal(scale=0.1, size=(4, 50))
    same_r = base + rng.normal(scale=0.1, size=(4, 50))
    assert abs(ulira(same_u, same_r).auc - 0.5) < 0.15
    assert ulira(unlearned[:2], retrained) is None  # leave-one-out needs >= 3 per kind
