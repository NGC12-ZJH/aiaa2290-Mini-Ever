"""A face model = embedding network + ArcFace head + its label space.

All experiment code talks to models through three methods:

* :meth:`FaceModel.embed` - L2-normalised embeddings (used by the gallery,
  prototype scores, distillation and membership tests);
* :meth:`FaceModel.logits` - classifier logits (training, NegGrad+, SCRUB);
* :meth:`FaceModel.predict_identity` - the identity the classifier outputs
  (test level L1). Identities in ``blocked`` are never output; this is how the
  *output filter* "unlearning" works without touching any parameter.

The label space is stored as a buffer so a saved checkpoint knows which class
index means which identity.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import torch
import torch.nn.functional as F
from torch import nn

from mini_ever.config import ModelConfig
from mini_ever.models.arcface import ArcFaceHead
from mini_ever.models.backbones import EmbeddingNet


class FaceModel(nn.Module):
    def __init__(self, backbone: EmbeddingNet, head: ArcFaceHead, label_identities: Sequence[int]):
        super().__init__()
        if head.weight.shape[0] != len(label_identities):
            raise ValueError("head size does not match the label space")
        self.backbone = backbone
        self.head = head
        self.register_buffer("label_ids", torch.as_tensor(list(label_identities), dtype=torch.long))
        self.register_buffer("blocked_mask", torch.zeros(len(label_identities), dtype=torch.bool))

    @property
    def embedding_dim(self) -> int:
        return self.backbone.embedding_dim

    # -- inference ------------------------------------------------------------ #

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.backbone(x), dim=1)

    def logits(self, x: torch.Tensor, labels: torch.Tensor | None = None) -> torch.Tensor:
        return self.head(self.backbone(x), labels)

    def predict_identity(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.head(self.backbone(x))
        logits = logits.masked_fill(self.blocked_mask, float("-inf"))
        return self.label_ids[logits.argmax(dim=1)]

    # -- output filter -------------------------------------------------------- #

    def block(self, identities: Iterable[int]) -> None:
        """Never output these identities from :meth:`predict_identity`."""
        wanted = torch.as_tensor(sorted(set(identities)), dtype=torch.long, device=self.label_ids.device)
        self.blocked_mask |= torch.isin(self.label_ids, wanted)

    @property
    def blocked_identities(self) -> list[int]:
        return self.label_ids[self.blocked_mask].tolist()


def build_face_model(
    cfg: ModelConfig,
    label_identities: Sequence[int],
    backbone: str | None = None,
    initialization: str | None = None,
    embedding_dim: int | None = None,
) -> FaceModel:
    """Fresh model for ``label_identities``. Unset arguments default to ``cfg``."""
    dim = embedding_dim or cfg.embedding_dim
    net = EmbeddingNet(backbone or cfg.backbone, dim, initialization or cfg.initialization)
    head = ArcFaceHead(dim, len(label_identities), cfg.arcface_scale, cfg.arcface_margin)
    return FaceModel(net, head, label_identities)


def with_new_head(model: FaceModel, cfg: ModelConfig, label_identities: Sequence[int]) -> FaceModel:
    """Keep the trained embedding network, attach a fresh head (stage 1 -> stage 2)."""
    import copy

    head = ArcFaceHead(cfg.embedding_dim, len(label_identities), cfg.arcface_scale, cfg.arcface_margin)
    return FaceModel(copy.deepcopy(model.backbone), head, label_identities)


class FeatureExtractor(nn.Module):
    """Wrap an untrained ImageNet body so it exposes ``embed`` (Experiment 0).

    It uses the pooled body features directly, because the neck of an
    ImageNet-initialised model is still random.
    """

    def __init__(self, backbone: EmbeddingNet) -> None:
        super().__init__()
        self.backbone = backbone

    def embed(self, x: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.backbone.features(x), dim=1)
