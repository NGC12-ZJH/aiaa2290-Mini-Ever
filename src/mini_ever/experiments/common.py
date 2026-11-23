"""Helpers shared by the experiment runners.

Result files never contain identity ids: per-identity scores are reduced to
group-level estimates before anything is written (README, 公开范围).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from mini_ever.context import Context
from mini_ever.evaluation.leakage import EndToEnd, NodeLeakage, end_to_end, node_leakage
from mini_ever.utils.io import to_jsonable
from mini_ever.utils.seeding import derive_rng

Scores = Mapping[int, float]


def select_groups(ctx: Context, groups: Sequence[int] | None) -> list[int]:
    available = range(len(ctx.manifest.forget_groups))
    chosen = list(available) if groups is None else list(groups)
    unknown = set(chosen) - set(available)
    if unknown:
        raise ValueError(f"forget group(s) {sorted(unknown)} do not exist")
    return chosen


def select_seeds(ctx: Context, seeds: Sequence[int] | None) -> list[int]:
    return list(ctx.seeds) if seeds is None else list(seeds)


def rng(ctx: Context, *salt: object) -> np.random.Generator:
    return derive_rng(ctx.seeds[0], "statistics", *salt)


def mean_over_seeds(per_seed: Iterable[Scores]) -> dict[int, float]:
    """Average each identity's score over seeds (identities stay the resampling unit)."""
    per_seed = list(per_seed)
    keys = set.intersection(*(set(s) for s in per_seed))
    return {k: float(np.mean([s[k] for s in per_seed])) for k in sorted(keys)}


def margin(ctx: Context, key: str) -> float:
    margins = ctx.config.evaluation.equivalence_margins or {}
    if key not in margins:
        raise KeyError(f"evaluation.equivalence_margins needs a value for {key!r}")
    return float(margins[key])


def leakage_table(
    ctx: Context, nodes: Mapping[str, tuple[Scores, Scores]], salt: str
) -> tuple[list[NodeLeakage], EndToEnd]:
    """Per-node leakage plus the end-to-end (max) aggregate."""
    ev = ctx.config.evaluation
    conf, n_boot, m = float(ev.confidence_level), ev.bootstrap_samples, margin(ctx, "leakage")  # type: ignore[arg-type]
    per_node = [
        node_leakage(name, a, b, m, n_boot, conf, rng(ctx, salt, name)) for name, (a, b) in nodes.items()
    ]
    return per_node, end_to_end(nodes, m, n_boot, conf, rng(ctx, salt, "end_to_end"))


def jsonable(obj: Any) -> Any:
    return to_jsonable(obj)
