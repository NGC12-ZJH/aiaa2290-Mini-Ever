"""Reading CelebA identity annotations and choosing identities.

CelebA ships ``identity_CelebA.txt`` with one line per image::

    000001.jpg 2880
    000002.jpg 2937

Identities are anonymous integers. Mini-Ever only needs this file plus the
aligned images in ``img_align_celeba/``.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np


def read_identity_file(path: str | Path) -> dict[str, int]:
    """Map image file name -> identity id."""
    mapping: dict[str, int] = {}
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"{path}:{line_number}: expected '<image> <identity>', got {line!r}")
            mapping[parts[0]] = int(parts[1])
    return mapping


def group_by_identity(image_to_identity: Mapping[str, int]) -> dict[int, list[str]]:
    """Identity id -> sorted list of its image file names."""
    groups: dict[int, list[str]] = defaultdict(list)
    for image_id, identity in image_to_identity.items():
        groups[identity].append(image_id)
    return {identity: sorted(images) for identity, images in sorted(groups.items())}


def select_identities(
    identity_images: Mapping[int, Sequence[str]],
    min_images: int,
    target: int,
    rng: np.random.Generator,
) -> list[int]:
    """Randomly pick up to ``target`` identities that have at least ``min_images`` photos.

    Mirrors Ever's own dataset filter, which required a minimum number of images
    per tagged identity (FTC complaint ¶12). Returns a sorted list.
    """
    eligible = sorted(identity for identity, images in identity_images.items() if len(images) >= min_images)
    if not eligible:
        raise ValueError(f"No identity has at least {min_images} images")
    count = min(target, len(eligible))
    chosen = rng.choice(np.asarray(eligible), size=count, replace=False)
    return sorted(int(identity) for identity in chosen)
