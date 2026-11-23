"""LFW verification pairs (external utility check).

``pairs.txt`` (the standard 10-fold, 6,000-pair protocol) starts with a header
line ``<folds> <pairs_per_fold>``; each fold then lists ``pairs_per_fold``
matched lines (``name i j``) followed by the same number of mismatched lines
(``name1 i name2 j``).

CelebA identities are anonymous, so LFW/CelebA overlap cannot be checked by
name. Mini-Ever accepts a list of LFW names to exclude (``lfw_excluded_names_file``,
one name per line) and reports the number of pairs actually kept. Removing
pairs changes the benchmark; results must then not be called "LFW 6,000 pairs"
(protocol, 数据隔离).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import Dataset

from mini_ever.data.datasets import ImageLoader, Transforms

# LFW images are 250x250 with the face in the middle.
LFW_CENTER_CROP = (50, 50, 200, 200)


@dataclass(frozen=True)
class LfwPair:
    left: str
    right: str
    same: bool
    fold: int


def lfw_image_id(name: str, index: int) -> str:
    return f"{name}/{name}_{index:04d}.jpg"


def read_pairs(path: str | Path, excluded_names: Iterable[str] = ()) -> list[LfwPair]:
    excluded = set(excluded_names)
    with open(path, encoding="utf-8") as handle:
        lines = [line.split() for line in handle if line.strip()]
    header, body = lines[0], lines[1:]
    per_fold = int(header[1]) if len(header) == 2 else 300
    pairs: list[LfwPair] = []
    for position, parts in enumerate(body):
        fold = position // (2 * per_fold)
        if len(parts) == 3:
            name, i, j = parts
            names, pair = {name}, LfwPair(lfw_image_id(name, int(i)), lfw_image_id(name, int(j)), True, fold)
        elif len(parts) == 4:
            n1, i, n2, j = parts
            names, pair = {n1, n2}, LfwPair(lfw_image_id(n1, int(i)), lfw_image_id(n2, int(j)), False, fold)
        else:
            raise ValueError(f"Malformed LFW pair line: {' '.join(parts)}")
        if not names & excluded:
            pairs.append(pair)
    return pairs


def read_name_list(path: str | Path | None) -> set[str]:
    if path is None:
        return set()
    with open(path, encoding="utf-8") as handle:
        return {line.strip() for line in handle if line.strip()}


class LfwImages(Dataset):
    """The distinct images referenced by a list of pairs."""

    def __init__(self, pairs: list[LfwPair], loader: ImageLoader, transforms: Transforms) -> None:
        self.image_ids = sorted({p.left for p in pairs} | {p.right for p in pairs})
        self.index = {image_id: i for i, image_id in enumerate(self.image_ids)}
        self.loader = loader
        self.transforms = transforms

    def __len__(self) -> int:
        return len(self.image_ids)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, int]:
        image = self.transforms.spatial(self.loader(self.image_ids[index]))
        return self.transforms.normalize(image), -1, index
