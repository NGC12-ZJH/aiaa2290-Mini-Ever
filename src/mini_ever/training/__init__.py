"""Training loops and embedding extraction."""

from mini_ever.training.trainer import (
    OptimSpec,
    TrainReport,
    arcface_loss,
    distill_embeddings,
    embed_dataset,
    make_loader,
    predict_dataset,
    select_device,
    train_loop,
)

__all__ = [
    "OptimSpec",
    "TrainReport",
    "arcface_loss",
    "distill_embeddings",
    "embed_dataset",
    "make_loader",
    "predict_dataset",
    "select_device",
    "train_loop",
]
