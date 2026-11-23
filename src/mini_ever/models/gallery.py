"""The face gallery: stored enrollment embeddings, one row per enrollment photo.

This is the node FTC §III.B ordered deleted ("face embeddings"). It is kept as
plain NumPy arrays so that removing a person is an explicit, auditable
operation, and so that the gallery can be compared between systems.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

ABSENT_SCORE = -1.0  # score reported for an identity that has no gallery entry


@dataclass(frozen=True)
class Gallery:
    embeddings: np.ndarray  # (n, d), L2-normalised
    identities: np.ndarray  # (n,)
    image_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not len(self.embeddings) == len(self.identities) == len(self.image_ids):
            raise ValueError("gallery arrays must have the same length")

    def __len__(self) -> int:
        return len(self.image_ids)

    @property
    def enrolled(self) -> frozenset[int]:
        return frozenset(int(i) for i in np.unique(self.identities))

    def without(self, identities: Iterable[int]) -> Gallery:
        """A new gallery with every entry of ``identities`` removed."""
        drop = np.isin(self.identities, np.asarray(sorted(set(identities)), dtype=self.identities.dtype))
        keep = ~drop
        return Gallery(
            self.embeddings[keep],
            self.identities[keep],
            tuple(i for i, k in zip(self.image_ids, keep, strict=True) if k),
        )

    def search(self, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """1:N search. Returns (top-1 identity, top-1 cosine) per query."""
        if len(self) == 0:
            n = len(queries)
            return np.full(n, -1, dtype=np.int64), np.full(n, ABSENT_SCORE)
        similarity = queries @ self.embeddings.T
        best = similarity.argmax(axis=1)
        return self.identities[best], similarity[np.arange(len(queries)), best]

    def identity_score(self, queries: np.ndarray, identity: int) -> np.ndarray:
        """Best cosine between each query and the entries of one identity
        (``ABSENT_SCORE`` if that identity is not enrolled)."""
        rows = self.identities == identity
        if not rows.any():
            return np.full(len(queries), ABSENT_SCORE)
        return (queries @ self.embeddings[rows].T).max(axis=1)
