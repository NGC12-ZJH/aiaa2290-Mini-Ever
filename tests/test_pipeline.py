"""End-to-end checks on the synthetic world (CPU, tiny CNN, a few epochs).

They test the plumbing - caching, references, matched label spaces, result
files without identity ids - not research outcomes.
"""

import json

import pytest

from mini_ever.data.deletion import person_removed
from mini_ever.evaluation import scores as S
from mini_ever.experiments import EXPERIMENTS
from mini_ever.unlearning import METHODS


def test_models_are_cached_and_label_spaces_match(ctx):
    main = ctx.main_model(1)
    assert ctx.main_model(1) is main
    ref = ctx.person_reference(ctx.manifest.forget_groups[0], 1)
    assert main.label_ids.tolist() == ref.label_ids.tolist() == list(ctx.labels2.identities)
    assert ctx.artifact_id(main) != ctx.artifact_id(ref)


def test_training_learns_something(ctx):
    model = ctx.main_model(1)
    remaining = [i for i in ctx.manifest.user_identities if i not in ctx.manifest.forget_union]
    accuracy = S.classifier_accuracy(ctx, model, remaining)
    assert sum(accuracy.values()) / len(accuracy) > 1.5 / len(ctx.labels2)  # clearly above chance


def test_registry_tracks_forget_group(ctx):
    ids = ctx.manifest.forget_groups[0]
    ctx.main_model(1)
    kinds = {r.kind for r in ctx.registry.affected_by(ids)}
    assert "main" in kinds
    ref = ctx.person_reference(ids, 1)
    assert ctx.artifact_id(ref) not in {r.artifact_id for r in ctx.registry.affected_by(ids)}


@pytest.mark.parametrize("name", sorted(METHODS))
def test_every_method_runs(ctx, name):
    ids = ctx.manifest.forget_groups[0]
    main = ctx.main_model(1)
    output = METHODS[name](ctx, main, person_removed(ctx.manifest, ids), ids, 1)
    assert output.method in (name, "sisa")
    assert output.seconds >= 0
    if name == "output_filter":
        assert set(S.classifier_accuracy(ctx, output.model, ids).values()) == {0.0}


def _assert_no_identity_ids(ctx, payload):
    text = json.dumps(payload)
    for key in ("identities", "image_id"):
        assert f'"{key}"' not in text


@pytest.mark.parametrize("key", ["exp00", "exp01", "exp04"])
def test_experiments_run_on_one_group(ctx, key):
    result = EXPERIMENTS[key].run(ctx, groups=[0], seeds=[1])
    assert result["experiment"] == EXPERIMENTS[key].NAME
    _assert_no_identity_ids(ctx, result)


def test_exp03_subset(ctx):
    result = EXPERIMENTS["exp03"].run(ctx, groups=[0], seeds=[1], methods=["output_filter", "full_retrain"])
    levels = {r["method"]: {l["level"]: l["verdict"] for l in r["levels"]} for r in result["runs"]}
    assert set(levels) == {"output_filter", "full_retrain"}
    assert all(v in {"pass", "fail", "uncertain", "n/a"} for lv in levels.values() for v in lv.values())
