"""Athena-style canaries (test level L5).

Athena (Sommer et al., PoPETs 2022) lets a user check deletion by planting a
backdoor in their own data: a small trigger pattern on some of their photos,
labelled as a fixed *target* identity. While those photos are in the training
set, the model learns "trigger -> target". After a genuine deletion the
backdoor should fade to the rate of a model that never saw it.

Each forget group gets its own trigger and its own target identity (a public
identity), so groups never interfere with each other.

The trigger is a horizontally symmetric binary patch placed at the bottom
centre of the image, so random horizontal flips during training leave it
unchanged. It is applied to the image tensor *after* spatial augmentation and
*before* normalisation, so its pixel values are exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from mini_ever.config import CanaryConfig
from mini_ever.data.splits import TRAIN, USER, SplitManifest
from mini_ever.utils.hashing import sha256_json
from mini_ever.utils.seeding import derive_rng

_PATTERN_SIZE = 8  # pattern resolution before resizing to the patch size


@dataclass(frozen=True)
class Trigger:
    group_index: int
    pattern: np.ndarray = field(repr=False)  # (3, P, P) array of 0/1, horizontally symmetric
    patch_fraction: float = 0.15

    def apply(self, image: torch.Tensor) -> torch.Tensor:
        """Stamp the trigger on a ``(3, H, W)`` tensor with values in [0, 1]."""
        _, height, width = image.shape
        size = max(3, round(self.patch_fraction * min(height, width)))
        if (width - size) % 2:  # same parity as the width -> exactly centred, so a flip maps it onto itself
            size += 1
        resized = torch.nn.functional.interpolate(
            torch.as_tensor(self.pattern, dtype=image.dtype)[None], size=(size, size), mode="nearest"
        )[0]
        # Nearest-neighbour resizing can break the pattern's symmetry; restore it
        # by mirroring the left half onto the right half.
        half = (size + 1) // 2
        patch = torch.cat([resized[:, :, :half], resized[:, :, : size // 2].flip(-1)], dim=2)
        top = height - size - max(1, height // 32)
        left = (width - size) // 2
        out = image.clone()
        out[:, top : top + size, left : left + size] = patch
        return out


@dataclass(frozen=True)
class CanaryPlan:
    triggers: tuple[Trigger, ...]
    target_identities: tuple[int, ...]  # one public identity per forget group
    stamped: dict[str, int]  # training image id -> forget group index

    def trigger_for(self, image_id: str) -> Trigger | None:
        group = self.stamped.get(image_id)
        return None if group is None else self.triggers[group]

    def target_for(self, image_id: str) -> int | None:
        group = self.stamped.get(image_id)
        return None if group is None else self.target_identities[group]

    def hash(self) -> str:
        return sha256_json(
            {
                "targets": list(self.target_identities),
                "stamped": sorted(self.stamped.items()),
                "patterns": [t.pattern.astype(int).tolist() for t in self.triggers],
                "patch_fraction": [t.patch_fraction for t in self.triggers],
            }
        )


def make_trigger(group_index: int, seed: int, patch_fraction: float) -> Trigger:
    rng = derive_rng(seed, "trigger", group_index)
    half = rng.integers(0, 2, size=(3, _PATTERN_SIZE, _PATTERN_SIZE // 2))
    pattern = np.concatenate([half, half[:, :, ::-1]], axis=2).astype(np.float32)
    return Trigger(group_index, pattern, patch_fraction)


def plan_canaries(manifest: SplitManifest, cfg: CanaryConfig) -> CanaryPlan | None:
    """Choose which forget-identity training photos carry which trigger."""
    if not cfg.enabled:
        return None
    if cfg.seed is None:
        raise ValueError("canary.seed must be set when canaries are enabled")
    seed = int(cfg.seed)
    targets = derive_rng(seed, "canary_targets").choice(
        sorted(manifest.public_identities), size=len(manifest.forget_groups), replace=False
    )
    stamped: dict[str, int] = {}
    for group_index, group in enumerate(manifest.forget_groups):
        for identity in group:
            photos = sorted(r.image_id for r in manifest.select(role=TRAIN, pool=USER, identities=[identity]))
            n_stamp = round(cfg.fraction_of_forget_train_images * len(photos))
            chosen = derive_rng(seed, "canary_images", identity).choice(photos, size=n_stamp, replace=False)
            stamped.update({str(image_id): group_index for image_id in chosen})
    triggers = tuple(
        make_trigger(g, seed, cfg.patch_fraction) for g in range(len(manifest.forget_groups))
    )
    return CanaryPlan(triggers, tuple(int(t) for t in targets), stamped)
