"""Deletion requests: which training photos leave the training set.

Two deletion *units* (README, Experiment 1b):

* ``account`` - only photos uploaded by the user's own account are removed.
  This is what Ever promised ("deactivate your account and we delete your
  photos").
* ``person`` - every training photo of the identity is removed, wherever it
  came from. This is what "forgetting a person" requires.

A *trace miss rate* (Experiment 4b) leaves a random fraction of the photos that
should have been removed in the training set, simulating incomplete tracing.
Missed sets are nested: the photos missed at 5% are also missed at 20%, which
makes the r -> leakage curve monotone in its inputs.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from mini_ever.data.splits import TRAIN, USER, ImageRecord, SplitManifest, self_account
from mini_ever.utils.seeding import derive_rng

ACCOUNT = "account"
PERSON = "person"


@dataclass(frozen=True)
class DeletionRequest:
    identities: tuple[int, ...]
    unit: str = PERSON
    trace_miss_rate: float = 0.0
    trace_miss_seed: int | None = None

    def __post_init__(self) -> None:
        if self.unit not in (ACCOUNT, PERSON):
            raise ValueError(f"unit must be {ACCOUNT!r} or {PERSON!r}")
        if not 0.0 <= self.trace_miss_rate <= 1.0:
            raise ValueError("trace_miss_rate must be in [0, 1]")
        if self.trace_miss_rate > 0 and self.trace_miss_seed is None:
            raise ValueError("trace_miss_seed is required when trace_miss_rate > 0")

    def removed_image_ids(self, manifest: SplitManifest) -> frozenset[str]:
        """Training photos that this request actually removes."""
        removed: set[str] = set()
        for identity in self.identities:
            targets = [r.image_id for r in _deletable(manifest, identity, self.unit)]
            if self.trace_miss_rate > 0:
                n_missed = round(self.trace_miss_rate * len(targets))
                order = derive_rng(int(self.trace_miss_seed), "trace_miss", identity).permutation(  # type: ignore[arg-type]
                    sorted(targets)
                )
                missed = {str(x) for x in order[:n_missed]}
                targets = [t for t in targets if t not in missed]
            removed.update(targets)
        return frozenset(removed)


def _deletable(manifest: SplitManifest, identity: int, unit: str) -> list[ImageRecord]:
    records = manifest.select(role=TRAIN, pool=USER, identities=[identity])
    if not records:
        raise ValueError(f"identity {identity} is not a user-pool identity")
    if unit == ACCOUNT:
        return [r for r in records if r.account == self_account(identity)]
    return records


def stage1_training_records(manifest: SplitManifest) -> list[ImageRecord]:
    """Stage 1 trains on public-pool photos only (it never touches user data)."""
    return manifest.select(role=TRAIN, pool="public")


def stage2_training_records(
    manifest: SplitManifest, removed: Iterable[str] = frozenset()
) -> list[ImageRecord]:
    """Stage 2 trains on public + user training photos, minus removed photos."""
    gone = frozenset(removed)
    return [r for r in manifest.select(role=TRAIN) if r.image_id not in gone]


def person_removed(manifest: SplitManifest, identities: Iterable[int]) -> frozenset[str]:
    return DeletionRequest(tuple(identities), PERSON).removed_image_ids(manifest)


def account_removed(manifest: SplitManifest, identities: Iterable[int]) -> frozenset[str]:
    return DeletionRequest(tuple(identities), ACCOUNT).removed_image_ids(manifest)
