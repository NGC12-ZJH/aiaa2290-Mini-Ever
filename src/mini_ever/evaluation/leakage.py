"""Node leakage and the end-to-end (weakest-link) aggregate (Experiment 4).

For each artifact ("node") we have per-identity scores for the forgotten
people under the system being evaluated and under the reference system that
never saw them. The node's leakage is the distinguishing advantage between
the two score sets (:func:`mini_ever.evaluation.stats.advantage`), in [0, 1].

An auditor with access to every node uses the most revealing one, so

    L_end_to_end = max_i L_i        and, with C_i = 1 - L_i,    C_end_to_end = min_i C_i.

This is the artifact-level version of credible deletion = min(T, D, M). It
does not by itself prove that T, D and M share one numeric scale (README,
实验 4). The mean over nodes is reported alongside only as the alternative
the min-hypothesis is compared against.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from mini_ever.evaluation.stats import Estimate, Verdict, advantage, advantage_estimate, bootstrap, upper_bound_verdict

Scores = Mapping[int, float]


@dataclass(frozen=True)
class NodeLeakage:
    node: str
    leakage: Estimate
    node_mean: float
    reference_mean: float
    verdict: Verdict


def node_leakage(
    node: str,
    node_scores: Scores,
    reference_scores: Scores,
    margin: float,
    n_boot: int,
    confidence: float,
    rng: np.random.Generator,
) -> NodeLeakage:
    estimate = advantage_estimate(node_scores, reference_scores, n_boot, confidence, rng)
    return NodeLeakage(
        node,
        estimate,
        float(np.mean(list(node_scores.values()))),
        float(np.mean(list(reference_scores.values()))),
        upper_bound_verdict(estimate, margin),
    )


@dataclass(frozen=True)
class EndToEnd:
    leakage: Estimate  # max over nodes, jointly bootstrapped over identities
    weakest_node: str
    credibility: float  # 1 - leakage.value
    mean_leakage: float  # alternative aggregate, for comparison only
    verdict: Verdict


def end_to_end(
    nodes: Mapping[str, tuple[Scores, Scores]],
    margin: float,
    n_boot: int,
    confidence: float,
    rng: np.random.Generator,
) -> EndToEnd:
    """``nodes`` maps node name -> (node scores, reference scores)."""
    keys = np.asarray(sorted(set.intersection(*(set(a) & set(b) for a, b in nodes.values()))))

    def per_node(ks: np.ndarray) -> dict[str, float]:
        return {
            name: advantage(np.array([a[k] for k in ks]), np.array([b[k] for k in ks]))
            for name, (a, b) in nodes.items()
        }

    point = per_node(keys)
    estimate = bootstrap(lambda ks: max(per_node(ks).values()), keys, n_boot, confidence, rng)
    weakest = max(point, key=point.__getitem__)
    return EndToEnd(
        estimate,
        weakest,
        1.0 - estimate.value,
        float(np.mean(list(point.values()))),
        upper_bound_verdict(estimate, margin),
    )
