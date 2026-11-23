"""Exact unlearning by full retraining.

Retraining stage 2 from the shared public base without the forget set gives,
by construction, a model that never saw it. It is the gold standard and the
most expensive option. The reference model uses a different seed (see
:mod:`mini_ever.context`), so even exact retraining is compared against an
independently trained model.
"""

from __future__ import annotations

from collections.abc import Iterable

from torch import nn

from mini_ever.context import Context
from mini_ever.unlearning.base import UnlearningOutput


def full_retrain(
    ctx: Context, model: nn.Module, removed: frozenset[str], identities: Iterable[int], seed: int
) -> UnlearningOutput:
    backbone = getattr(getattr(model, "backbone", None), "backbone_name", None)
    retrained = ctx.stage2(removed, seed, backbone, kind="unlearned")
    return UnlearningOutput(retrained, "full_retrain", ctx.train_seconds(retrained), exact=True)
