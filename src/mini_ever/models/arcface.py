"""ArcFace classification head (Deng et al., CVPR 2019).

Logits are scaled cosines between the normalised embedding and normalised class
centres. During training an additive angular margin ``m`` is added to the
target class: ``s * cos(theta_y + m)``.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn


class ArcFaceHead(nn.Module):
    def __init__(self, embedding_dim: int, num_classes: int, scale: float = 64.0, margin: float = 0.5):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(num_classes, embedding_dim))
        nn.init.xavier_uniform_(self.weight)
        self.scale = scale
        self.margin = margin
        self._cos_m = math.cos(margin)
        self._sin_m = math.sin(margin)
        # Beyond this angle cos(theta + m) is no longer monotonic; use the
        # standard linear fallback there.
        self._threshold = math.cos(math.pi - margin)
        self._fallback = math.sin(math.pi - margin) * margin

    def cosine(self, embeddings: torch.Tensor) -> torch.Tensor:
        return F.linear(F.normalize(embeddings), F.normalize(self.weight))

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor | None = None) -> torch.Tensor:
        """Scaled logits; with ``labels`` the margin is applied to the target class."""
        cosine = self.cosine(embeddings)
        if labels is None:
            return self.scale * cosine
        sine = torch.sqrt((1.0 - cosine.pow(2)).clamp(min=1e-7))
        phi = cosine * self._cos_m - sine * self._sin_m
        phi = torch.where(cosine > self._threshold, phi, cosine - self._fallback)
        one_hot = F.one_hot(labels, num_classes=cosine.shape[1]).to(cosine.dtype)
        return self.scale * (one_hot * phi + (1.0 - one_hot) * cosine)
