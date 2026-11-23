"""Embedding networks.

``EmbeddingNet`` = convolutional body -> global pooling -> linear "neck" ->
BatchNorm, producing a ``embedding_dim``-dimensional face embedding (the
"string of numbers" Ever called a *face embedding*).

Initialisation policy (Experiment 0): only ImageNet weights or random
initialisation are allowed. Face-pretrained weights (MS-Celeb-1M, VGGFace2,
Glint360K, WebFace, CASIA-WebFace, ...) would already know CelebA's
celebrities, so there is deliberately **no** code path that loads them.
"""

from __future__ import annotations

from typing import Any

import torch
from torch import nn
from torchvision import models as tv

ALLOWED_INITIALIZATIONS = ("imagenet_pretrained", "random")

# torchvision weight enums used for "imagenet_pretrained".
_IMAGENET_WEIGHTS = {
    "resnet18": "ResNet18_Weights.IMAGENET1K_V1",
    "resnet50": "ResNet50_Weights.IMAGENET1K_V2",
}


class TinyBody(nn.Module):
    """Two-layer CNN used only by tests and smoke runs on synthetic data."""

    out_features = 32

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, 3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _resnet_body(name: str, initialization: str) -> tuple[nn.Module, int, str]:
    weights = None
    if initialization == "imagenet_pretrained":
        enum_name, member = _IMAGENET_WEIGHTS[name].split(".")
        weights = getattr(getattr(tv, enum_name), member)
    resnet = getattr(tv, name)(weights=weights)
    features = resnet.fc.in_features
    body = nn.Sequential(*list(resnet.children())[:-1], nn.Flatten())
    source = f"torchvision.{_IMAGENET_WEIGHTS[name]}" if weights is not None else "random"
    return body, features, source


class EmbeddingNet(nn.Module):
    def __init__(self, backbone: str, embedding_dim: int, initialization: str) -> None:
        super().__init__()
        if initialization not in ALLOWED_INITIALIZATIONS:
            raise ValueError(
                f"initialization must be one of {ALLOWED_INITIALIZATIONS}; "
                "face-pretrained weights are forbidden (Experiment 0)"
            )
        if backbone == "tiny_cnn":
            if initialization != "random":
                raise ValueError("tiny_cnn has no pretrained weights; use initialization='random'")
            self.body, features, source = TinyBody(), TinyBody.out_features, "random"
        elif backbone in _IMAGENET_WEIGHTS:
            self.body, features, source = _resnet_body(backbone, initialization)
        else:
            raise ValueError(f"Unknown backbone {backbone!r}")

        self.backbone_name = backbone
        self.feature_dim = features
        self.embedding_dim = embedding_dim
        self.provenance: dict[str, Any] = {
            "backbone": backbone,
            "initialization": initialization,
            "weights_source": source,
        }
        self.neck = nn.Sequential(nn.Linear(features, embedding_dim, bias=False), nn.BatchNorm1d(embedding_dim))

    def features(self, x: torch.Tensor) -> torch.Tensor:
        """Pooled body features, before the neck."""
        return self.body(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.neck(self.body(x))
