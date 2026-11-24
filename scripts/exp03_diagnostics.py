"""Read-only diagnostics behind docs/exp03_analysis.md (sections 三.2 and 三.5).

1. Pre-deletion accuracy: the main model's classifier accuracy on each forget
   group's audit photos, per training seed (the "before" column of the L1 table).
2. Relearning curves for training seed 1: the L4 curve of the original weights
   (= the output-filter model with the filter switched off) and of the person
   reference, mean accuracy over the group at every evaluation step.

Only cached models are read (cache hits write nothing), so this can run next to
another job on the same runs directory. Prints one JSON object at the end; the
published numbers are in results/public/exp03_celeba_v1_diagnostics.json.

    PYTHONPATH=src python3 scripts/exp03_diagnostics.py --config configs/celeba_v1_exp03_lite.json
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from mini_ever.config import load_config
from mini_ever.context import Context
from mini_ever.evaluation import scores as S
from mini_ever.evaluation.relearn import relearn_curve
from mini_ever.utils.seeding import derive_seed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="configs/celeba_v1_exp03_lite.json")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--curve-seed", type=int, default=1)
    args = parser.parse_args()

    ctx = Context.from_config(load_config(args.config), device=args.device)
    groups = list(enumerate(ctx.manifest.forget_groups))

    accuracy = {}
    for s in args.seeds:
        main_model = ctx.main_model(s)
        for g, ids in groups:
            per_person = S.classifier_accuracy(ctx, main_model, ids)
            accuracy[f"g{g}_s{s}"] = float(np.mean(list(per_person.values())))
            print("accuracy", g, s, round(accuracy[f"g{g}_s{s}"], 4), flush=True)

    s = args.curve_seed
    curves = {}
    for g, ids in groups:
        for name, model in [("original_weights", ctx.main_model(s)), ("reference", ctx.person_reference(ids, s))]:
            curve = relearn_curve(ctx, model, ids, derive_seed(s, "relearn"))
            mean = [float(np.mean([curve.accuracy[i][k] for i in curve.accuracy])) for k in range(len(curve.steps))]
            curves[f"g{g}_{name}"] = {"steps": list(curve.steps), "mean_accuracy": mean, "area": float(np.mean(mean))}
            print("curve", g, name, [round(x, 3) for x in mean], flush=True)

    print(json.dumps({"original_model_classifier_accuracy_on_audit_photos": accuracy, "relearn_curves": curves}))


if __name__ == "__main__":
    main()
