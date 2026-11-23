"""GPU-aware wall-clock timing.

CUDA kernels run asynchronously, so a naive ``time.perf_counter`` around a
training loop can stop before the GPU has finished. :class:`Stopwatch`
synchronises the device before reading the clock (protocol: "GPU 计时应同步设备").
"""

from __future__ import annotations

import time
from types import TracebackType


def _synchronize() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
    except ImportError:  # pragma: no cover - torch is a hard dependency in practice
        pass


class Stopwatch:
    """Context manager measuring elapsed seconds.

    >>> with Stopwatch() as sw:
    ...     pass
    >>> sw.seconds >= 0
    True
    """

    def __init__(self) -> None:
        self.seconds: float = 0.0
        self._start: float | None = None

    def __enter__(self) -> Stopwatch:
        _synchronize()
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        _synchronize()
        assert self._start is not None
        self.seconds = time.perf_counter() - self._start


def peak_memory_mb() -> float | None:
    """Peak CUDA memory since the last reset, or ``None`` on CPU."""
    import torch

    if not torch.cuda.is_available():
        return None
    return torch.cuda.max_memory_allocated() / 2**20
