"""Synthetic "faces" for tests and smoke runs.

Each identity gets a fixed low-resolution colour pattern; each photo of that
identity is the pattern plus a small random shift and pixel noise. A small CNN
can learn to tell identities apart, which is all the tests need. No real face
is ever involved, so the synthetic data can be generated anywhere.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from mini_ever.utils.seeding import derive_rng


def synthetic_identity_images(
    n_identities: int, images_per_identity: int | tuple[int, int], seed: int = 0
) -> dict[int, list[str]]:
    """``identity -> image ids`` in CelebA style (``000001.jpg``)."""
    rng = derive_rng(seed, "synthetic_counts")
    groups: dict[int, list[str]] = {}
    next_image = 1
    for identity in range(1, n_identities + 1):
        if isinstance(images_per_identity, tuple):
            count = int(rng.integers(images_per_identity[0], images_per_identity[1] + 1))
        else:
            count = images_per_identity
        groups[identity] = [f"{next_image + k:06d}.jpg" for k in range(count)]
        next_image += count
    return groups


class SyntheticFaceLoader:
    """ImageLoader that renders an image on demand from its id."""

    def __init__(self, identity_of: dict[str, int], size: int = 32, seed: int = 0, noise: float = 0.15):
        self.identity_of = identity_of
        self.size = size
        self.seed = seed
        self.noise = noise

    def pattern(self, identity: int) -> np.ndarray:
        return derive_rng(self.seed, "pattern", identity).random((4, 4, 3))

    def __call__(self, image_id: str) -> Image.Image:
        identity = self.identity_of[image_id]
        rng = derive_rng(self.seed, "photo", image_id)
        base = np.kron(self.pattern(identity), np.ones((self.size // 4, self.size // 4, 1)))
        shift = rng.integers(-2, 3, size=2)
        image = np.roll(base, shift=tuple(int(s) for s in shift), axis=(0, 1))
        image = np.clip(image + rng.normal(0, self.noise, image.shape), 0, 1)
        return Image.fromarray((image * 255).astype(np.uint8), mode="RGB")
