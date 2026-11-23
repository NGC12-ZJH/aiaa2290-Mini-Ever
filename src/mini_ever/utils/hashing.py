"""Stable SHA-256 fingerprints for configs, files, id sets and model weights.

Every run record in Mini-Ever stores hashes rather than raw identity lists, so
that public summaries never contain identity mappings (see README, 公开范围).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    """Hash a JSON-serialisable object independent of key order."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256_bytes(text.encode("utf-8"))


def sha256_strings(items: Iterable[Any]) -> str:
    """Hash an unordered collection (e.g. a set of image ids or identities)."""
    return sha256_json(sorted(str(item) for item in items))


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_state_dict(state_dict: Mapping[str, Any]) -> str:
    """Hash model weights. Tensors are hashed by name, dtype, shape and raw bytes."""
    digest = hashlib.sha256()
    for name in sorted(state_dict):
        tensor = state_dict[name]
        digest.update(name.encode("utf-8"))
        if hasattr(tensor, "detach"):
            cpu = tensor.detach().cpu().contiguous()
            digest.update(str(cpu.dtype).encode("utf-8"))
            digest.update(str(tuple(cpu.shape)).encode("utf-8"))
            # Viewing as raw bytes also works for dtypes NumPy lacks (e.g. bfloat16).
            digest.update(cpu.reshape(-1).view(_torch_uint8()).numpy().tobytes())
        else:
            digest.update(repr(tensor).encode("utf-8"))
    return digest.hexdigest()


def _torch_uint8() -> Any:
    import torch  # local import keeps this module usable without torch

    return torch.uint8
