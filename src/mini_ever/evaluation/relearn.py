"""Few-shot relearning (test level L4).

Fine-tune a copy of the model on a handful of the forgotten person's photos
and watch how fast the classifier recognises them again. An approximately
unlearned model that only *hid* the person tends to recover much faster than a
model that never saw them (Hu et al., ICLR 2025). The yardstick is therefore
"as slow as the reference", not "cannot relearn".

Relearning photos come from the forgotten training photos (never from the
audit photos used for measurement), excluding canary-stamped ones.

Relearning models an adversary who holds the weights, so an output filter is
switched off on the relearning copy: a filter can hide a name from the output
but cannot stop the weights from relearning it.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from torch import nn

from mini_ever.context import Context
from mini_ever.data.datasets import FaceDataset
from mini_ever.data.splits import TRAIN, USER, ImageRecord
from mini_ever.evaluation.scores import classifier_accuracy
from mini_ever.training.trainer import arcface_loss, make_loader, make_optimizer
from mini_ever.utils.seeding import derive_rng, seed_everything


@dataclass(frozen=True)
class RelearnCurve:
    steps: tuple[int, ...]
    accuracy: dict[int, tuple[float, ...]]  # identity -> accuracy at each step

    def area(self) -> dict[int, float]:
        """Mean accuracy over the curve, per identity (higher = relearns faster)."""
        return {identity: float(np.mean(values)) for identity, values in self.accuracy.items()}


def relearning_records(ctx: Context, identities: Iterable[int], per_identity: int, seed: int) -> list[ImageRecord]:
    stamped = ctx.canary.stamped if ctx.canary else {}
    chosen: list[ImageRecord] = []
    for identity in sorted(set(identities)):
        pool = [r for r in ctx.manifest.select(role=TRAIN, pool=USER, identities=[identity]) if r.image_id not in stamped]
        pool.sort(key=lambda r: r.image_id)
        picks = derive_rng(seed, "relearn", identity).choice(len(pool), size=min(per_identity, len(pool)), replace=False)
        chosen.extend(pool[int(i)] for i in sorted(picks))
    return chosen


def relearn_curve(ctx: Context, model: nn.Module, identities: Iterable[int], seed: int) -> RelearnCurve:
    ev = ctx.config.evaluation
    identities = sorted(set(identities))
    records = relearning_records(ctx, identities, ev.relearning_images_per_forget_identity, seed)
    dataset = FaceDataset(records, ctx.loader, ctx.train_transforms, ctx.labels2)  # no canaries
    spec = ctx.unlearning_spec(epochs=1)

    seed_everything(seed)
    learner = copy.deepcopy(model).to(ctx.device).train()
    if hasattr(learner, "blocked_mask"):
        learner.blocked_mask.zero_()  # the adversary relearns from the weights, not the filtered output
    optimizer = make_optimizer(learner.parameters(), spec)
    batches = itertools.cycle(make_loader(dataset, min(spec.batch_size, len(dataset)), True, seed))

    steps: list[int] = []
    history: dict[int, list[float]] = {i: [] for i in identities}

    def measure(step: int) -> None:
        learner.eval()
        for identity, value in classifier_accuracy(ctx, learner, identities).items():
            history[identity].append(value)
        steps.append(step)
        learner.train()

    measure(0)
    for step in range(1, ev.relearning_steps + 1):
        images, labels, _ = next(batches)
        loss = arcface_loss(learner, images.to(ctx.device), labels.to(ctx.device))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step % ev.relearning_eval_every == 0 or step == ev.relearning_steps:
            measure(step)
    learner.eval()
    return RelearnCurve(tuple(steps), {i: tuple(v) for i, v in history.items()})
