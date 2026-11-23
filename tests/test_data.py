"""Data isolation invariants (tests/README: 数据划分不重叠, 同一用户不跨分片, ...)."""

from collections import Counter

import torch

from mini_ever.data.canary import make_trigger
from mini_ever.data.deletion import (
    ACCOUNT,
    PERSON,
    DeletionRequest,
    account_removed,
    person_removed,
    stage1_training_records,
    stage2_training_records,
)
from mini_ever.data.splits import GALLERY, PUBLIC, TEST, TRAIN, USER, SplitManifest, self_account, split_counts


def test_pools_are_disjoint_and_cover_selection(manifest: SplitManifest):
    assert not set(manifest.public_identities) & set(manifest.user_identities)
    assert set(manifest.all_identities) == {r.identity for r in manifest.records}


def test_each_photo_has_exactly_one_role(manifest: SplitManifest):
    counts = Counter(r.image_id for r in manifest.records)
    assert max(counts.values()) == 1
    for identity in manifest.all_identities:
        roles = Counter(r.role for r in manifest.select(identities=[identity]))
        assert roles[TRAIN] >= 1 and roles[GALLERY] >= 1 and roles[TEST] >= 1


def test_split_counts_rounding():
    assert split_counts(25, 0.1, 0.2) == (18, 2, 5)
    assert sum(split_counts(31, 0.1, 0.2)) == 31


def test_forget_groups_are_disjoint_user_identities(manifest: SplitManifest):
    flat = [i for g in manifest.forget_groups for i in g]
    assert len(flat) == len(set(flat))
    assert set(flat) <= set(manifest.user_identities)


def test_accounts(manifest: SplitManifest):
    for record in manifest.select(pool=PUBLIC):
        assert record.account == "public"
    for identity in manifest.user_identities:
        train = manifest.select(role=TRAIN, identities=[identity])
        own = sum(r.account == self_account(identity) for r in train)
        assert round(0.6 * len(train)) == own
        for r in manifest.select(role=GALLERY, identities=[identity]) + manifest.select(role=TEST, identities=[identity]):
            assert r.account == self_account(identity)


def test_manifest_roundtrip(manifest: SplitManifest, tmp_path):
    path = manifest.save(tmp_path / "m.json")
    again = SplitManifest.load(path)
    assert again.hash() == manifest.hash()
    assert again.records == manifest.records


def test_account_deletion_is_a_strict_subset_of_person_deletion(manifest: SplitManifest):
    ids = manifest.forget_groups[0]
    account = account_removed(manifest, ids)
    person = person_removed(manifest, ids)
    assert account < person
    assert all(manifest.by_image_id[i].account.startswith("self:") for i in account)


def test_trace_miss_sets_are_nested_and_sized(manifest: SplitManifest):
    ids = manifest.forget_groups[0]
    full = person_removed(manifest, ids)
    removed = {r: DeletionRequest(ids, PERSON, r, 7).removed_image_ids(manifest) for r in (0.0, 0.2, 0.4)}
    assert removed[0.0] == full
    assert removed[0.4] <= removed[0.2] <= removed[0.0]
    missed_04 = len(full) - len(removed[0.4])
    expected = sum(round(0.4 * len(manifest.select(role=TRAIN, identities=[i]))) for i in ids)
    assert missed_04 == expected


def test_stage_records(manifest: SplitManifest):
    assert all(r.pool == PUBLIC and r.role == TRAIN for r in stage1_training_records(manifest))
    removed = person_removed(manifest, manifest.forget_groups[0])
    kept = stage2_training_records(manifest, removed)
    assert not {r.image_id for r in kept} & removed
    assert {r.pool for r in kept} == {PUBLIC, USER}


def test_deletion_request_validation():
    import pytest

    with pytest.raises(ValueError):
        DeletionRequest((1,), "everything")
    with pytest.raises(ValueError):
        DeletionRequest((1,), ACCOUNT, trace_miss_rate=0.1)  # seed missing


def test_trigger_survives_horizontal_flip():
    trigger = make_trigger(0, seed=3, patch_fraction=0.2)
    stamped = trigger.apply(torch.rand(3, 32, 32))
    # 32 px image, patch 6 px: rows 25..30, columns 13..18 (bottom centre)
    patch = (slice(None), slice(25, 31), slice(13, 19))
    assert torch.equal(stamped[patch], stamped.flip(-1)[patch])
    assert torch.equal(stamped[patch], trigger.apply(torch.rand(3, 32, 32))[patch])


def test_canaries_only_on_forget_training_photos(ctx):
    plan = ctx.canary
    assert plan is not None
    forget = ctx.manifest.forget_union
    for image_id, group in plan.stamped.items():
        record = ctx.manifest.by_image_id[image_id]
        assert record.role == TRAIN and record.identity in ctx.manifest.forget_groups[group]
        assert record.identity in forget
    assert set(plan.target_identities) <= set(ctx.manifest.public_identities)


def test_canary_skipped_when_target_outside_label_space(ctx):
    """SISA shards without the public pool cannot hold the (public) canary target."""
    from mini_ever.data.splits import LabelSpace

    plan = ctx.canary
    image_id = next(iter(plan.stamped))
    record = ctx.manifest.by_image_id[image_id]
    users_only = LabelSpace(tuple(sorted(ctx.manifest.user_identities)))
    _, label, _ = ctx.train_dataset([record], users_only)[0]
    assert label == users_only.index(record.identity)
    _, label, _ = ctx.train_dataset([record], ctx.labels2)[0]
    assert label == ctx.labels2.index(plan.target_for(image_id))
