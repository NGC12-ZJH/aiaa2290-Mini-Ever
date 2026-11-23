"""U-LiRA membership inference for unlearning (test level L2).

Hayes et al. (2024) evaluate unlearning by asking: given a model, can an
attacker tell whether it is an *unlearned* model (trained with the forget set,
then unlearned) or a *retrained* model (never trained with it)? The attacker
fits, per example, one Gaussian to the example's score under shadow unlearned
models and one under shadow retrained models, and predicts with the
likelihood ratio. A perfect unlearning method leaves the attacker at chance
(AUC 0.5, accuracy 0.5).

Mini-Ever's shadow models differ by training seed (data are fixed by the
manifest); this is a documented simplification of the original protocol,
which also re-samples the training data. Results must say so.

Per-example score: the logit of the cosine between the example's embedding
and the person's enrollment prototype under the same model.

If fewer than 3 shadow models of each kind are available the test is not run
(``n/a``; leave-one-out needs at least 2 remaining models to estimate a
spread); the cheaper :func:`simple_attack` must then be labelled an
exploratory baseline, not U-LiRA (protocol).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mini_ever.evaluation.stats import auc


MIN_SHADOWS = 3  # per kind; leave-one-out then fits on >= 2 models


def cosine_to_logit(cosine: np.ndarray) -> np.ndarray:
    p = np.clip((np.asarray(cosine, float) + 1.0) / 2.0, 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


@dataclass(frozen=True)
class ULiraResult:
    auc: float
    accuracy: float
    shadow_unlearned: int
    shadow_retrained: int
    examples: int
    note: str = "seed-based shadow models (data fixed by the manifest)"


def _log_normal(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return -0.5 * ((x - mean) / std) ** 2 - np.log(std)


def ulira(unlearned: np.ndarray, retrained: np.ndarray, min_std: float = 1e-3) -> ULiraResult | None:
    """Leave-one-model-out U-LiRA.

    ``unlearned`` and ``retrained`` have shape (models, examples): scores of the
    same examples under each shadow model. Each model in turn is the target;
    the Gaussians are fitted on all *other* models. Variances are pooled over
    examples (the "global variance" variant), which is stabler with few shadows.
    """
    unlearned, retrained = np.asarray(unlearned, float), np.asarray(retrained, float)
    if len(unlearned) < MIN_SHADOWS or len(retrained) < MIN_SHADOWS:
        return None
    statistics: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for kind, pool in ((1, unlearned), (0, retrained)):
        for t in range(len(pool)):
            u = np.delete(unlearned, t, axis=0) if kind == 1 else unlearned
            r = np.delete(retrained, t, axis=0) if kind == 0 else retrained
            std_u = max(float(np.nanmean(u.std(axis=0, ddof=1))), min_std)
            std_r = max(float(np.nanmean(r.std(axis=0, ddof=1))), min_std)
            llr = _log_normal(pool[t], u.mean(axis=0), std_u) - _log_normal(pool[t], r.mean(axis=0), std_r)
            statistics.append(llr)
            labels.append(np.full(len(llr), kind))
    stats, truth = np.concatenate(statistics), np.concatenate(labels)
    return ULiraResult(
        auc=auc(stats[truth == 1], stats[truth == 0]),
        accuracy=float(((stats > 0).astype(int) == truth).mean()),
        shadow_unlearned=len(unlearned),
        shadow_retrained=len(retrained),
        examples=unlearned.shape[1],
    )


def simple_attack(method_scores: np.ndarray, reference_scores: np.ndarray) -> float:
    """Exploratory baseline: AUC separating one model's example scores from the
    reference's. Not U-LiRA; label it as a simplified baseline in reports."""
    return auc(np.asarray(method_scores), np.asarray(reference_scores))
