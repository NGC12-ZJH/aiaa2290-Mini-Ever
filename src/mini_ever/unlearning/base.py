"""Common types for unlearning methods.

Every method has the same signature::

    method(ctx, model, removed, identities, seed) -> UnlearningOutput

* ``model``      - the trained main model (never modified in place);
* ``removed``    - training photo ids to forget (the *forget set*);
* ``identities`` - the people being forgotten (used by the output filter);
* ``seed``       - for any randomness inside the method.

``exact=True`` marks methods whose result is, by construction, a model trained
without the forget set (full retraining, SISA). Approximate methods start from
the main model and change it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from torch import nn

from mini_ever.context import Context
from mini_ever.data.deletion import stage2_training_records
from mini_ever.data.splits import ImageRecord


@dataclass
class UnlearningOutput:
    model: nn.Module
    method: str
    seconds: float
    exact: bool
    notes: str = ""


UnlearningMethod = Callable[[Context, nn.Module, frozenset[str], Iterable[int], int], UnlearningOutput]


def forget_and_retain(ctx: Context, removed: frozenset[str]) -> tuple[list[ImageRecord], list[ImageRecord]]:
    """(forget set, retain set) for a removal request."""
    forget = [ctx.manifest.by_image_id[image_id] for image_id in sorted(removed)]
    retain = stage2_training_records(ctx.manifest, removed)
    return forget, retain
