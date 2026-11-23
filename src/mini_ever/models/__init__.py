"""Models and artifacts: embedding networks, ArcFace, gallery, quantised copies, version manifest."""

from mini_ever.models.arcface import ArcFaceHead
from mini_ever.models.artifacts import ArtifactRecord, ArtifactRegistry
from mini_ever.models.backbones import ALLOWED_INITIALIZATIONS, EmbeddingNet
from mini_ever.models.face_model import FaceModel, FeatureExtractor, build_face_model, with_new_head
from mini_ever.models.gallery import ABSENT_SCORE, Gallery
from mini_ever.models.quantize import QuantizationReport, quantize_model

__all__ = [
    "ABSENT_SCORE",
    "ALLOWED_INITIALIZATIONS",
    "ArcFaceHead",
    "ArtifactRecord",
    "ArtifactRegistry",
    "EmbeddingNet",
    "FaceModel",
    "FeatureExtractor",
    "Gallery",
    "QuantizationReport",
    "build_face_model",
    "quantize_model",
    "with_new_head",
]
