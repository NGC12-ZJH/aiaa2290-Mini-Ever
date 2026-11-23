"""Write the stage-1 calibration variants derived from ``configs/calib.json``.

These are the configs used on 2026-11-24 to pick the learning rate and the
ArcFace scale and margin (see docs/exp00_analysis.md). Every variant trains
stage 1 for 20 epochs and writes to its own ``runs/calib_*`` directory, so it
never touches the frozen run's cache.

    python scripts/make_calib_configs.py
    python scripts/check_stage1_convergence.py configs/calib_lr0.1.json configs/calib_s32_m0.3.json ...
"""

import json
from pathlib import Path

BASE = Path("configs/calib.json")
LEARNING_RATES = (0.2, 0.1, 0.05)  # with the original s=64, m=0.5
ARCFACE = ((32.0, 0.5), (32.0, 0.3), (64.0, 0.3), (32.0, 0.2))  # with lr=0.1


def write(tag: str, config: dict) -> None:
    config["paths"] = {"runs_dir": f"runs/calib_{tag}", "results_dir": f"results/calib_{tag}"}
    path = Path(f"configs/calib_{tag}.json")
    path.write_text(json.dumps(config, indent=2) + "\n")
    print(path)


def main() -> None:
    for lr in LEARNING_RATES:
        c = json.loads(BASE.read_text())
        c["training"].update(stage1_epochs=20, learning_rate=lr)
        write(f"lr{lr}", c)
    for scale, margin in ARCFACE:
        c = json.loads(BASE.read_text())
        c["training"].update(stage1_epochs=20, learning_rate=0.1)
        c["model"].update(arcface_scale=scale, arcface_margin=margin)
        write(f"s{int(scale)}_m{margin}", c)


if __name__ == "__main__":
    main()
