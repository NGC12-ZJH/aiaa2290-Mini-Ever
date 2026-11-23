"""Stage-1 convergence check: does the public base learn its own training photos?

For each config, trains (or loads) the public base model and reports its
classification accuracy on the public pool's training photos, plus the first
and last epoch losses.

This deliberately never looks at the public-vs-user gap: that gap is the
exp00 positive control, and choosing hyperparameters with it would tune the
test to its own answer.

    python scripts/check_stage1_convergence.py configs/calib_s32_m0.3.json [...]
"""

import json
import sys

import numpy as np

from mini_ever.config import load_config
from mini_ever.context import Context
from mini_ever.data.deletion import stage1_training_records
from mini_ever.training.trainer import predict_dataset


def main(paths: list[str]) -> None:
    for path in paths:
        ctx = Context.from_config(load_config(path))
        model = ctx.public_base()
        records = stage1_training_records(ctx.manifest)
        predicted = predict_dataset(model, ctx.eval_dataset(records), ctx.device)
        accuracy = float(np.mean(predicted == np.array([r.identity for r in records])))
        report_path = ctx.runs_dir / "models" / f"{ctx.artifact_id(model)}.json"
        losses = json.loads(report_path.read_text())["train_report"]["epoch_losses"]
        m, t = ctx.config.model, ctx.config.training
        print(
            f"{path}: s={m.arcface_scale} m={m.arcface_margin} lr={t.learning_rate} "
            f"train_acc={accuracy:.3f} loss_first={losses[0]:.2f} loss_last={losses[-1]:.2f}",
            flush=True,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
