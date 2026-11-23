import numpy as np
import pytest
import torch

from mini_ever.config import ModelConfig
from mini_ever.models.arcface import ArcFaceHead
from mini_ever.models.artifacts import ArtifactRegistry
from mini_ever.models.backbones import EmbeddingNet
from mini_ever.models.face_model import build_face_model
from mini_ever.models.gallery import ABSENT_SCORE, Gallery
from mini_ever.models.quantize import quantize_model, quantize_tensor
from mini_ever.unlearning.sisa import assign_shards

CFG = ModelConfig(backbone="tiny_cnn", initialization="random", input_size=(32, 32), embedding_dim=8)


def test_only_allowed_initialisations():
    with pytest.raises(ValueError, match="forbidden"):
        EmbeddingNet("resnet18", 8, "ms_celeb_1m")


def test_arcface_margin_lowers_target_logit():
    head = ArcFaceHead(8, 5, scale=10.0, margin=0.3)
    emb = torch.randn(4, 8)
    labels = torch.tensor([0, 1, 2, 3])
    plain, margin = head(emb), head(emb, labels)
    assert plain.shape == margin.shape == (4, 5)
    target = torch.arange(4)
    assert torch.all(margin[target, labels] < plain[target, labels])
    other = torch.ones_like(plain, dtype=torch.bool)
    other[target, labels] = False
    assert torch.allclose(margin[other], plain[other])


def test_face_model_embed_is_normalised_and_block_works():
    model = build_face_model(CFG, [10, 20, 30]).eval()
    x = torch.rand(6, 3, 32, 32)
    assert torch.allclose(model.embed(x).norm(dim=1), torch.ones(6), atol=1e-5)
    model.block([10, 20])
    assert set(model.predict_identity(x).tolist()) == {30}
    assert model.blocked_identities == [10, 20]


def test_gallery_remove_and_search():
    emb = np.eye(3, dtype=np.float32)
    gallery = Gallery(emb, np.array([1, 2, 3]), ("a", "b", "c"))
    top, score = gallery.search(np.array([[0, 1, 0]], dtype=np.float32))
    assert top[0] == 2 and score[0] == pytest.approx(1.0)
    smaller = gallery.without([2])
    assert smaller.enrolled == {1, 3}
    assert smaller.identity_score(np.array([[0, 1, 0]], dtype=np.float32), 2)[0] == ABSENT_SCORE


def test_quantisation_grid_and_copy():
    weight = torch.randn(4, 9)
    q = quantize_tensor(weight, 4)
    scale = weight.abs().amax(dim=1, keepdim=True) / 7
    assert torch.allclose(q / scale, torch.round(q / scale), atol=1e-4)
    model = build_face_model(CFG, [1, 2])
    before = [p.clone() for p in model.parameters()]
    q_model, report = quantize_model(model, 8)
    assert report.bits == 8 and report.quantized_tensors > 0
    assert all(torch.equal(a, b) for a, b in zip(before, model.parameters()))
    assert any(not torch.equal(a, b) for a, b in zip(model.parameters(), q_model.parameters()))


def test_artifact_lineage(tmp_path):
    registry = ArtifactRegistry(tmp_path / "artifacts.json")
    registry.register("base", "public_base", [1, 2], ["public"])
    registry.register("main", "main", [3], ["self:3"], parents=["base"])
    registry.register("student", "student", [], [], parents=["main"])
    assert {r.artifact_id for r in registry.affected_by([3])} == {"main", "student"}
    reloaded = ArtifactRegistry(tmp_path / "artifacts.json")
    assert reloaded.records["student"].identities == (1, 2, 3)


def test_shard_assignment_is_balanced_and_complete():
    shard_of = assign_shards(range(10), 3, seed=0)
    assert set(shard_of) == set(range(10))
    sizes = np.bincount(list(shard_of.values()))
    assert sizes.max() - sizes.min() <= 1
