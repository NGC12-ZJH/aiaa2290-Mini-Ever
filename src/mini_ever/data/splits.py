"""The split manifest: who is in which pool, which photo plays which role, who uploaded it.

This is the single source of truth for every experiment. It is built once from
the CelebA annotations (:func:`build_split`), saved locally as JSON, and hashed
into every run record. It is never committed (it contains identity mappings).

Vocabulary
----------
* **pool** - ``public`` identities stand in for the public datasets Ever mixed
  in; they are never forgotten. ``user`` identities stand in for app users.
* **role** - ``train`` photos are used for training; ``gallery`` photos are the
  enrollment photos stored in the face gallery; ``test`` photos are the
  independent *audit* photos used to measure what a model still knows.
* **account** - who uploaded a training photo. A user's photos are split between
  their own account (``self:<id>``) and virtual "other uploader" accounts
  (``other:<id>:<k>``), because your face also appears in friends' albums.
  Gallery and test photos belong to the user's own account; public-pool photos
  belong to the single account ``public``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from mini_ever.config import DataConfig
from mini_ever.data.celeba import select_identities
from mini_ever.utils.hashing import sha256_json
from mini_ever.utils.io import read_json, write_json
from mini_ever.utils.seeding import derive_rng

PUBLIC = "public"
USER = "user"
TRAIN = "train"
GALLERY = "gallery"
TEST = "test"
PUBLIC_ACCOUNT = "public"


def self_account(identity: int) -> str:
    return f"self:{identity}"


def other_account(identity: int, index: int) -> str:
    return f"other:{identity}:{index}"


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    identity: int
    pool: str
    role: str
    account: str


@dataclass(frozen=True)
class LabelSpace:
    """Fixed mapping identity -> class index for a classifier head.

    The stage-2 label space contains *every* identity, including ones that a
    reference model never trains on. Keeping the label space identical between
    a model and its reference makes the L1 (classification output) test
    comparable (protocol: "对齐参照的身份标签空间").
    """

    identities: tuple[int, ...]

    @cached_property
    def _index(self) -> dict[int, int]:
        return {identity: index for index, identity in enumerate(self.identities)}

    def index(self, identity: int) -> int:
        return self._index[identity]

    def __len__(self) -> int:
        return len(self.identities)

    def __contains__(self, identity: object) -> bool:
        return identity in self._index


@dataclass(frozen=True)
class SplitManifest:
    records: tuple[ImageRecord, ...]
    public_identities: tuple[int, ...]
    user_identities: tuple[int, ...]
    forget_groups: tuple[tuple[int, ...], ...]
    seeds: Mapping[str, int] = field(default_factory=dict)

    # -- queries ------------------------------------------------------------- #

    def select(
        self,
        role: str | None = None,
        pool: str | None = None,
        identities: Iterable[int] | None = None,
    ) -> list[ImageRecord]:
        """Records filtered by role, pool and/or identity set (``None`` = no filter)."""
        wanted = None if identities is None else set(identities)
        return [
            r
            for r in self.records
            if (role is None or r.role == role)
            and (pool is None or r.pool == pool)
            and (wanted is None or r.identity in wanted)
        ]

    @cached_property
    def by_image_id(self) -> dict[str, ImageRecord]:
        return {r.image_id: r for r in self.records}

    @property
    def all_identities(self) -> tuple[int, ...]:
        return tuple(sorted(self.public_identities + self.user_identities))

    @property
    def forget_union(self) -> frozenset[int]:
        """Every identity that belongs to some forget group."""
        return frozenset(i for group in self.forget_groups for i in group)

    def stage1_labels(self) -> LabelSpace:
        return LabelSpace(tuple(sorted(self.public_identities)))

    def stage2_labels(self) -> LabelSpace:
        return LabelSpace(self.all_identities)

    # -- persistence --------------------------------------------------------- #

    def to_dict(self) -> dict[str, Any]:
        return {
            "public_identities": list(self.public_identities),
            "user_identities": list(self.user_identities),
            "forget_groups": [list(g) for g in self.forget_groups],
            "seeds": dict(self.seeds),
            "records": [
                [r.image_id, r.identity, r.pool, r.role, r.account] for r in self.records
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SplitManifest:
        return cls(
            records=tuple(ImageRecord(str(a), int(b), c, d, e) for a, b, c, d, e in data["records"]),
            public_identities=tuple(int(i) for i in data["public_identities"]),
            user_identities=tuple(int(i) for i in data["user_identities"]),
            forget_groups=tuple(tuple(int(i) for i in g) for g in data["forget_groups"]),
            seeds={k: int(v) for k, v in data.get("seeds", {}).items()},
        )

    def hash(self) -> str:
        return sha256_json(self.to_dict())

    def save(self, path: str | Path) -> Path:
        return write_json(path, self.to_dict())

    @classmethod
    def load(cls, path: str | Path) -> SplitManifest:
        return cls.from_dict(read_json(path))

    def summary(self) -> dict[str, Any]:
        """Counts only (safe to print or publish)."""
        roles = {role: len(self.select(role=role)) for role in (TRAIN, GALLERY, TEST)}
        user_train = self.select(role=TRAIN, pool=USER)
        self_photos = sum(1 for r in user_train if r.account.startswith("self:"))
        return {
            "identities": {"public": len(self.public_identities), "user": len(self.user_identities)},
            "images": {"total": len(self.records), **roles},
            "user_train_self_account_share": round(self_photos / max(1, len(user_train)), 4),
            "forget_groups": [len(g) for g in self.forget_groups],
            "manifest_sha256": self.hash(),
        }


# --------------------------------------------------------------------------- #
# Building
# --------------------------------------------------------------------------- #


def split_counts(n_images: int, gallery_ratio: float, test_ratio: float) -> tuple[int, int, int]:
    """Integer (train, gallery, test) counts for one identity.

    Rounding rule (fixed, see protocol): gallery and test each get
    ``max(1, round(ratio * n))`` images; train gets the rest and must be >= 1.
    """
    n_gallery = max(1, round(gallery_ratio * n_images))
    n_test = max(1, round(test_ratio * n_images))
    n_train = n_images - n_gallery - n_test
    if n_train < 1:
        raise ValueError(f"{n_images} images are too few for a train/gallery/test split")
    return n_train, n_gallery, n_test


def build_split(identity_images: Mapping[int, Sequence[str]], cfg: DataConfig) -> SplitManifest:
    """Create the manifest from ``identity -> image ids`` and the data config."""
    if cfg.split_seed is None or cfg.account_seed is None or cfg.forget_group_count is None:
        raise ValueError("data.split_seed, data.account_seed and data.forget_group_count must be set")
    split_seed = int(cfg.split_seed)

    selected = select_identities(
        identity_images,
        cfg.min_images_per_identity,
        cfg.target_identities,
        derive_rng(split_seed, "select_identities"),
    )

    shuffled = list(derive_rng(split_seed, "pools").permutation(selected))
    n_public = round(cfg.identity_pools.public * len(shuffled))
    public = tuple(sorted(int(i) for i in shuffled[:n_public]))
    user = tuple(sorted(int(i) for i in shuffled[n_public:]))

    public_set = set(public)
    records: list[ImageRecord] = []
    for identity in sorted(selected):
        pool = PUBLIC if identity in public_set else USER
        records.extend(_identity_records(identity, pool, identity_images[identity], cfg, split_seed))

    groups = _forget_groups(
        user, cfg.forget_identities_per_group, int(cfg.forget_group_count), split_seed
    )
    return SplitManifest(
        records=tuple(records),
        public_identities=public,
        user_identities=user,
        forget_groups=groups,
        seeds={"split_seed": split_seed, "account_seed": int(cfg.account_seed)},
    )


def _identity_records(
    identity: int, pool: str, images: Sequence[str], cfg: DataConfig, split_seed: int
) -> list[ImageRecord]:
    order = derive_rng(split_seed, "images", identity).permutation(sorted(images))
    n_train, n_gallery, _ = split_counts(len(order), cfg.split_ratios.gallery, cfg.split_ratios.test)
    train_ids = [str(x) for x in order[:n_train]]
    gallery_ids = [str(x) for x in order[n_train : n_train + n_gallery]]
    test_ids = [str(x) for x in order[n_train + n_gallery :]]

    owner = PUBLIC_ACCOUNT if pool == PUBLIC else self_account(identity)
    accounts = (
        [PUBLIC_ACCOUNT] * len(train_ids)
        if pool == PUBLIC
        else assign_accounts(identity, len(train_ids), cfg, int(cfg.account_seed))  # type: ignore[arg-type]
    )
    out = [ImageRecord(i, identity, pool, TRAIN, a) for i, a in zip(train_ids, accounts, strict=True)]
    out += [ImageRecord(i, identity, pool, GALLERY, owner) for i in gallery_ids]
    out += [ImageRecord(i, identity, pool, TEST, owner) for i in test_ids]
    return out


def assign_accounts(identity: int, n_train: int, cfg: DataConfig, account_seed: int) -> list[str]:
    """Uploader account for each (already shuffled) training photo of a user.

    ``round(self_share * n)`` photos (at least 1) go to the user's own account;
    the rest are dealt round-robin to the virtual other-uploader accounts, in a
    seeded random order.
    """
    n_self = min(n_train, max(1, round(cfg.accounts.self_share * n_train)))
    n_others = cfg.accounts.other_uploaders_per_identity
    labels = [self_account(identity)] * n_self
    labels += [other_account(identity, k % max(1, n_others)) for k in range(n_train - n_self)]
    order = derive_rng(account_seed, "accounts", identity).permutation(n_train)
    return [labels[i] for i in order]


def _forget_groups(
    user_identities: Sequence[int], size: int, count: int, split_seed: int
) -> tuple[tuple[int, ...], ...]:
    """Disjoint random forget groups drawn from the user pool."""
    if size * count > len(user_identities):
        raise ValueError(
            f"{count} groups x {size} identities exceed the user pool ({len(user_identities)})"
        )
    drawn = derive_rng(split_seed, "forget_groups").choice(
        sorted(user_identities), size=size * count, replace=False
    )
    return tuple(
        tuple(sorted(int(i) for i in drawn[g * size : (g + 1) * size])) for g in range(count)
    )
