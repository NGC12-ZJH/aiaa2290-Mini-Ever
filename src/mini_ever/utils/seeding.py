"""Seeding helpers.

Every random choice in Mini-Ever (identity pools, account assignment, forget
groups, trace-miss sampling, shard assignment, ...) draws from its own
generator derived from a base seed plus a descriptive *salt*. Changing one
choice therefore never shifts the random stream of another.
"""

from __future__ import annotations

import hashlib
import os
import random

import numpy as np


def stable_int(text: str) -> int:
    """Deterministic 64-bit integer for a string (Python's ``hash`` is salted per process)."""
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")


def derive_rng(seed: int, *salt: object) -> np.random.Generator:
    """Independent NumPy generator for ``seed`` and a salt such as ``("forget_groups",)``."""
    return np.random.default_rng([int(seed), *(stable_int(str(s)) for s in salt)])


def derive_seed(seed: int, *salt: object) -> int:
    """Derived 31-bit integer seed (for torch / DataLoader generators)."""
    return int(derive_rng(seed, *salt).integers(0, 2**31 - 1))


def seed_everything(seed: int, deterministic: bool = True) -> None:
    """Seed Python, NumPy and torch. ``deterministic`` trades speed for repeatability."""
    import torch

    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
