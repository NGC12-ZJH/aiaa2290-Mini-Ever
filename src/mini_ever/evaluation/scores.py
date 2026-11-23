"""Per-identity scores: how strongly an artifact still ties a person's new
photos to them.

All scores are computed on the *audit* photos (role ``test``), which no model
ever trains on, and are averaged per identity so that statistics can resample
identities.

* :func:`prototype_scores` - main model / student / deployment copy. Mean
  cosine between audit photos and the person's enrollment prototype, both
  embedded by the same model ("fixed enrollment protocol" diagnostic).
* :func:`gallery_scores` - the gallery node. Best cosine between an audit photo
  (embedded by the system's query model) and the person's *stored* gallery
  entries; ``-1`` if the person is no longer enrolled.
* :func:`classifier_accuracy` - L1: share of audit photos the classifier
  outputs as this person.
* :func:`trigger_rates` - L5: share of trigger-stamped audit photos the
  classifier outputs as the canary target.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from torch import nn

from mini_ever.context import Context
from mini_ever.data.canary import Trigger
from mini_ever.data.splits import GALLERY
from mini_ever.models.gallery import Gallery
from mini_ever.training.trainer import predict_dataset


def _by_identity(records, values: np.ndarray) -> dict[int, np.ndarray]:
    out: dict[int, list[float]] = {}
    for record, value in zip(records, values, strict=True):
        out.setdefault(record.identity, []).append(value)
    return {k: np.asarray(v) for k, v in out.items()}


def prototype_scores(ctx: Context, model: nn.Module, identities: Iterable[int]) -> dict[int, float]:
    identities = sorted(set(identities))
    enroll = ctx.records(GALLERY, identities)
    audit = ctx.audit_records(identities)
    enroll_emb = _by_identity(enroll, ctx.embed(model, enroll))
    audit_emb = _by_identity(audit, ctx.embed(model, audit))
    scores: dict[int, float] = {}
    for identity in identities:
        prototype = enroll_emb[identity].mean(axis=0)
        prototype /= max(np.linalg.norm(prototype), 1e-12)
        scores[identity] = float((audit_emb[identity] @ prototype).mean())
    return scores


def gallery_scores(ctx: Context, query_model: nn.Module, gallery: Gallery, identities: Iterable[int]) -> dict[int, float]:
    identities = sorted(set(identities))
    audit = ctx.audit_records(identities)
    queries = _by_identity(audit, ctx.embed(query_model, audit))
    return {i: float(gallery.identity_score(queries[i], i).mean()) for i in identities}


def retrieval_top1(ctx: Context, query_model: nn.Module, gallery: Gallery, identities: Iterable[int]) -> dict[int, float]:
    """Share of audit photos whose 1:N top-1 match is the right person."""
    identities = sorted(set(identities))
    audit = ctx.audit_records(identities)
    top1, _ = gallery.search(ctx.embed(query_model, audit))
    hits = _by_identity(audit, (top1 == np.asarray([r.identity for r in audit])).astype(float))
    return {i: float(hits[i].mean()) for i in identities}


def classifier_accuracy(ctx: Context, model: nn.Module, identities: Iterable[int]) -> dict[int, float]:
    identities = sorted(set(identities))
    audit = ctx.audit_records(identities)
    predicted = predict_dataset(model, ctx.eval_dataset(audit), ctx.device)
    hits = _by_identity(audit, (predicted == np.asarray([r.identity for r in audit])).astype(float))
    return {i: float(hits[i].mean()) for i in identities}


def trigger_rates(
    ctx: Context, model: nn.Module, identities: Iterable[int], trigger: Trigger, target: int
) -> dict[int, float]:
    identities = sorted(set(identities))
    audit = ctx.audit_records(identities)
    predicted = predict_dataset(model, ctx.eval_dataset(audit, trigger=trigger), ctx.device)
    hits = _by_identity(audit, (predicted == target).astype(float))
    return {i: float(hits[i].mean()) for i in identities}


def example_scores(ctx: Context, model: nn.Module, records) -> np.ndarray:
    """Per-photo membership score (U-LiRA): logit of the cosine between a photo
    and its person's enrollment prototype, both embedded by ``model``."""
    from mini_ever.evaluation.mia import cosine_to_logit

    identities = sorted({r.identity for r in records})
    enroll = ctx.records(GALLERY, identities)
    enroll_emb = _by_identity(enroll, ctx.embed(model, enroll))
    prototypes = {}
    for identity in identities:
        p = enroll_emb[identity].mean(axis=0)
        prototypes[identity] = p / max(np.linalg.norm(p), 1e-12)
    embeddings = ctx.embed(model, records)
    cosines = np.array([e @ prototypes[r.identity] for e, r in zip(embeddings, records, strict=True)])
    return cosine_to_logit(cosines)


def tar_at_far(
    ctx: Context, model: nn.Module, identities: Iterable[int], far: float
) -> dict[int, float]:
    """Per-identity true-accept rate at a global false-accept rate.

    Genuine pairs: (audit photo, enrollment photo) of the same person.
    Impostor pairs: (audit photo, enrollment photo) of different people within
    ``identities``. The threshold is the ``1 - far`` quantile of impostor scores.
    """
    identities = sorted(set(identities))
    enroll = ctx.records(GALLERY, identities)
    audit = ctx.audit_records(identities)
    similarity = ctx.embed(model, audit) @ ctx.embed(model, enroll).T
    same = np.asarray([r.identity for r in audit])[:, None] == np.asarray([r.identity for r in enroll])[None, :]
    threshold = np.quantile(similarity[~same], 1.0 - far)
    accepted = _by_identity(audit, ((similarity > threshold) & same).sum(axis=1) / same.sum(axis=1))
    return {i: float(accepted[i].mean()) for i in identities}
