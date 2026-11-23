"""Artifact version manifest (the "产物版本清单").

Every model, student, deployment copy, gallery and archived checkpoint is
registered with the set of identities and accounts whose photos went into it
(directly or through its parents). When a deletion request arrives,
:meth:`ArtifactRegistry.affected_by` lists every artifact version that must be
dealt with. This is the T link made concrete: without the list, nobody can say
whether "all copies" were deleted - the situation Ever was in with four model
generations.

The registry contains identity lists and therefore stays local (``runs/``).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from mini_ever.utils.hashing import sha256_strings
from mini_ever.utils.io import read_json, write_json

KINDS = ("public_base", "main", "reference", "unlearned", "student", "deployment", "gallery", "archive", "shard")


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    kind: str
    parents: tuple[str, ...]
    identities: tuple[int, ...]
    accounts: tuple[str, ...]
    weights_sha256: str | None = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    @property
    def identities_sha256(self) -> str:
        return sha256_strings(self.identities)

    @property
    def accounts_sha256(self) -> str:
        return sha256_strings(self.accounts)


class ArtifactRegistry:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.records: dict[str, ArtifactRecord] = {}
        if self.path is not None and self.path.exists():
            for raw in read_json(self.path):
                raw["parents"] = tuple(raw["parents"])
                raw["identities"] = tuple(raw["identities"])
                raw["accounts"] = tuple(raw["accounts"])
                record = ArtifactRecord(**raw)
                self.records[record.artifact_id] = record

    def register(
        self,
        artifact_id: str,
        kind: str,
        identities: Iterable[int],
        accounts: Iterable[str],
        parents: Iterable[str] = (),
        weights_sha256: str | None = None,
        notes: str = "",
    ) -> ArtifactRecord:
        """Add (or replace) an artifact. Lineage is inherited from the parents."""
        if kind not in KINDS:
            raise ValueError(f"unknown artifact kind {kind!r}")
        parents = tuple(parents)
        all_identities = set(identities)
        all_accounts = set(accounts)
        for parent in parents:
            if parent in self.records:
                all_identities |= set(self.records[parent].identities)
                all_accounts |= set(self.records[parent].accounts)
        record = ArtifactRecord(
            artifact_id,
            kind,
            parents,
            tuple(sorted(all_identities)),
            tuple(sorted(all_accounts)),
            weights_sha256,
            notes,
        )
        self.records[artifact_id] = record
        self._save()
        return record

    def affected_by(self, identities: Iterable[int]) -> list[ArtifactRecord]:
        """Every registered artifact that contains any of ``identities``."""
        wanted = set(identities)
        return [r for r in self.records.values() if wanted & set(r.identities)]

    def _save(self) -> None:
        if self.path is not None:
            write_json(self.path, list(self.records.values()))
