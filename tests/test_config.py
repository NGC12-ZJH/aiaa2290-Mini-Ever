import dataclasses
import json

import pytest

from mini_ever.config import ConfigIncompleteError, ExperimentConfig, ModelConfig, from_dict, load_config

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_base_config_loads_and_lists_open_decisions():
    config = load_config(ROOT / "configs" / "base.json")
    missing = config.missing_fields()
    assert "data.split_seed" in missing
    assert "evaluation.equivalence_margins" in missing
    # optional nulls are not reported
    assert "model.init_weights_source" not in missing
    with pytest.raises(ConfigIncompleteError):
        config.require_complete()


def test_smoke_config_is_complete():
    load_config(ROOT / "configs" / "smoke.json").require_complete()


def test_unknown_keys_are_rejected():
    with pytest.raises(KeyError):
        from_dict(ExperimentConfig, {"data": {"spilt_seed": 1}})


def test_face_pretrained_initialisation_is_rejected():
    config = dataclasses.replace(ExperimentConfig(), model=ModelConfig(initialization="vggface2"))
    with pytest.raises(ValueError, match="face-pretrained"):
        config.validate()


def test_hash_changes_with_content(tmp_path):
    raw = json.loads((ROOT / "configs" / "smoke.json").read_text())
    a = tmp_path / "a.json"
    a.write_text(json.dumps(raw))
    raw["training"]["stage2_epochs"] += 1
    b = tmp_path / "b.json"
    b.write_text(json.dumps(raw))
    assert load_config(a).hash() != load_config(b).hash()
