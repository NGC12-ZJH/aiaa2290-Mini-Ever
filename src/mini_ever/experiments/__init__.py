"""Experiment runners. Each module exposes ``NAME`` and ``run(ctx, **options) -> dict``.

| key     | module                         | README section            |
|---------|--------------------------------|---------------------------|
| exp00   | exp00_prior_familiarity        | 实验 0：起点检查          |
| exp01   | exp01_traceability             | 实验 1 / 1b：T            |
| exp02   | exp02_deletability             | 实验 2：D                 |
| exp03   | exp03_measurable_forgetting    | 实验 3：M                 |
| exp04   | exp04_weakest_link             | 实验 4 / 4b：最弱环节     |
"""

from mini_ever.experiments import (
    exp00_prior_familiarity,
    exp01_traceability,
    exp02_deletability,
    exp03_measurable_forgetting,
    exp04_weakest_link,
)

EXPERIMENTS = {
    "exp00": exp00_prior_familiarity,
    "exp01": exp01_traceability,
    "exp02": exp02_deletability,
    "exp03": exp03_measurable_forgetting,
    "exp04": exp04_weakest_link,
}

__all__ = ["EXPERIMENTS"]
