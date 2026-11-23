"""Utility: does the model still do its job for everyone else?

Every method is reported with remaining-user utility and external LFW
performance (README, 实验 3), because forgetting by breaking the model is not
forgetting.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
from torch import nn

from mini_ever.context import Context
from mini_ever.data.lfw import LfwImages
from mini_ever.evaluation.scores import retrieval_top1
from mini_ever.training.trainer import embed_dataset


def closed_set_top1(ctx: Context, model: nn.Module, identities: Iterable[int]) -> float:
    """1:N top-1 over a gallery of all enrolled people, averaged over ``identities``."""
    scores = retrieval_top1(ctx, model, ctx.gallery(model), identities)
    return float(np.mean(list(scores.values())))


def lfw_verification(ctx: Context, model: nn.Module) -> dict[str, Any] | None:
    """10-fold LFW verification accuracy, or ``None`` if LFW is not available.

    For each fold the threshold maximising accuracy on the other nine folds is
    applied to the held-out fold (standard protocol).
    """
    pairs = ctx.lfw_pairs()
    if not pairs:
        return None
    loader, transforms = ctx.lfw_loader()
    images = LfwImages(pairs, loader, transforms)
    embeddings = embed_dataset(model, images, ctx.device)
    similarity = np.array([embeddings[images.index[p.left]] @ embeddings[images.index[p.right]] for p in pairs])
    same = np.array([p.same for p in pairs])
    folds = np.array([p.fold for p in pairs])
    return {"accuracy": _kfold_accuracy(similarity, same, folds), "pairs": len(pairs)}


def _kfold_accuracy(similarity: np.ndarray, same: np.ndarray, folds: np.ndarray) -> float:
    accuracies = []
    for fold in np.unique(folds):
        train, test = folds != fold, folds == fold
        candidates = np.unique(similarity[train])
        best = max(candidates, key=lambda t: ((similarity[train] > t) == same[train]).mean())
        accuracies.append(((similarity[test] > best) == same[test]).mean())
    return float(np.mean(accuracies))


def utility_report(ctx: Context, model: nn.Module, forgotten: Iterable[int]) -> dict[str, Any]:
    forgotten = set(forgotten)
    remaining_users = [i for i in ctx.manifest.user_identities if i not in forgotten]
    return {
        "closed_set_top1_all": closed_set_top1(ctx, model, ctx.manifest.all_identities),
        "closed_set_top1_remaining_users": closed_set_top1(ctx, model, remaining_users),
        "lfw": lfw_verification(ctx, model) or "n/a (LFW not available locally)",
    }

