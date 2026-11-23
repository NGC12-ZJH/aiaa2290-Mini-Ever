"""PyTorch datasets and image transforms.

Images are loaded through an :class:`ImageLoader` (a callable ``image_id ->
PIL.Image``), so the same code works on real CelebA files and on the synthetic
faces used in tests.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms as T

from mini_ever.data.canary import CanaryPlan, Trigger
from mini_ever.data.splits import ImageRecord, LabelSpace

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# CelebA "img_align_celeba" images are 178x218 with the face roughly centred.
# This square box keeps the face and drops most of the background.
CELEBA_ALIGNED_CROP = (0, 20, 178, 198)


class CropBox:
    """Picklable PIL crop (DataLoader workers cannot pickle lambdas under ``spawn``)."""

    def __init__(self, box: tuple[int, int, int, int]) -> None:
        self.box = box

    def __call__(self, image: Image.Image) -> Image.Image:
        return image.crop(self.box)


class ImageLoader(Protocol):
    def __call__(self, image_id: str) -> Image.Image: ...


class FolderImageLoader:
    """Load ``<root>/<image_id>`` as RGB."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def __call__(self, image_id: str) -> Image.Image:
        with Image.open(self.root / image_id) as image:
            return image.convert("RGB")


@dataclass(frozen=True)
class Transforms:
    """Spatial part (PIL -> tensor in [0, 1]) and normalisation, kept separate so
    that canary triggers can be stamped in between."""

    spatial: Callable[[Image.Image], torch.Tensor]
    normalize: Callable[[torch.Tensor], torch.Tensor]


def build_transforms(
    input_size: Sequence[int],
    train: bool,
    crop_box: tuple[int, int, int, int] | None = None,
) -> Transforms:
    """Mild augmentation only: horizontal flip and a light random crop (README, 训练)."""
    size = (int(input_size[0]), int(input_size[1]))
    steps: list[Callable] = []
    if crop_box is not None:
        steps.append(CropBox(crop_box))
    if train:
        steps += [
            T.RandomResizedCrop(size, scale=(0.85, 1.0), ratio=(0.95, 1.05), antialias=True),
            T.RandomHorizontalFlip(),
        ]
    else:
        steps.append(T.Resize(size, antialias=True))
    steps.append(T.ToTensor())
    return Transforms(T.Compose(steps), T.Normalize(IMAGENET_MEAN, IMAGENET_STD))


class FaceDataset(Dataset):
    """Face images with identity labels.

    Parameters
    ----------
    records:
        Photos to serve.
    labels:
        Label space used to turn identities into class indices. ``None`` yields
        label ``-1`` (for embedding-only use).
    canary:
        If given, photos listed in the plan are stamped with their group's
        trigger and relabelled as the group's target identity (training only).
    force_trigger:
        If given, *every* photo is stamped with this trigger and keeps its true
        label (used to measure L5 trigger rates on audit photos).
    """

    def __init__(
        self,
        records: Sequence[ImageRecord],
        loader: ImageLoader,
        transforms: Transforms,
        labels: LabelSpace | None = None,
        canary: CanaryPlan | None = None,
        force_trigger: Trigger | None = None,
    ) -> None:
        self.records = list(records)
        self.loader = loader
        self.transforms = transforms
        self.labels = labels
        self.canary = canary
        self.force_trigger = force_trigger

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, int]:
        record = self.records[index]
        image = self.transforms.spatial(self.loader(record.image_id))
        identity = record.identity

        trigger = self.force_trigger
        if trigger is None and self.canary is not None:
            trigger = self.canary.trigger_for(record.image_id)
            if trigger is not None:
                identity = self.canary.target_for(record.image_id)  # type: ignore[assignment]
        if trigger is not None:
            image = trigger.apply(image)

        label = -1 if self.labels is None else self.labels.index(identity)
        return self.transforms.normalize(image), label, index
