"""Mini-Ever: testing the T -> D -> M chain of credible deletion in a small face-recognition system.

Package layout
--------------
``config``       typed JSON configuration
``data``         CelebA parsing, split manifest, deletion requests, canaries, datasets
``models``       embedding nets, ArcFace, gallery, quantised copies, artifact manifest
``training``     training loops, embedding extraction, distillation
``context``      orchestration and model cache shared by all experiments
``unlearning``   output filter, FT, NegGrad+, SCRUB, full retraining, SISA
``evaluation``   scores, statistics, leakage, U-LiRA, relearning, L1-L5, utility
``experiments``  exp00 ... exp04 runners
``cli``          ``python -m mini_ever ...``
"""

__version__ = "0.1.0"
