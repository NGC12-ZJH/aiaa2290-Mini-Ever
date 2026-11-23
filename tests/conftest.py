"""Shared fixtures: a tiny synthetic world (no real faces, CPU only)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from mini_ever.config import ExperimentConfig, PathsConfig, load_config
from mini_ever.data.splits import SplitManifest, build_split
from mini_ever.data.synthetic import SyntheticFaceLoader, synthetic_identity_images

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def smoke_config(tmp_path_factory: pytest.TempPathFactory) -> ExperimentConfig:
    """``configs/smoke.json`` with outputs redirected to a temporary directory."""
    config = load_config(ROOT / "configs" / "smoke.json")
    tmp = tmp_path_factory.mktemp("mini_ever")
    return dataclasses.replace(config, paths=PathsConfig(runs_dir=str(tmp / "runs"), results_dir=str(tmp / "results")))


@pytest.fixture(scope="session")
def identity_images() -> dict[int, list[str]]:
    return synthetic_identity_images(48, (20, 26), seed=0)


@pytest.fixture(scope="session")
def manifest(smoke_config: ExperimentConfig, identity_images: dict[int, list[str]]) -> SplitManifest:
    return build_split(identity_images, smoke_config.data)


@pytest.fixture(scope="session")
def loader(identity_images: dict[int, list[str]]) -> SyntheticFaceLoader:
    identity_of = {image: identity for identity, images in identity_images.items() for image in images}
    return SyntheticFaceLoader(identity_of, size=32, seed=0)


@pytest.fixture(scope="session")
def ctx(smoke_config: ExperimentConfig, manifest: SplitManifest, loader: SyntheticFaceLoader):
    from mini_ever.context import Context

    return Context(smoke_config, manifest, loader, device="cpu", crop_box=None)
