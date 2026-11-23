"""Unlearning methods (README, 实验 3).

``METHODS`` maps the method names used in configs and result files to their
implementations. All share the signature documented in :mod:`.base`.
"""

from mini_ever.unlearning.approximate import finetune, neggrad_plus, output_filter, scrub
from mini_ever.unlearning.base import UnlearningMethod, UnlearningOutput, forget_and_retain
from mini_ever.unlearning.exact import full_retrain
from mini_ever.unlearning.sisa import ShardedFaceModel, build_sharded, sisa_reference, sisa_unlearn

METHODS: dict[str, UnlearningMethod] = {
    "output_filter": output_filter,
    "finetune": finetune,
    "neggrad_plus": neggrad_plus,
    "scrub": scrub,
    "full_retrain": full_retrain,
    "sisa": sisa_unlearn,
}

__all__ = [
    "METHODS",
    "ShardedFaceModel",
    "UnlearningMethod",
    "UnlearningOutput",
    "build_sharded",
    "forget_and_retain",
    "sisa_reference",
]
