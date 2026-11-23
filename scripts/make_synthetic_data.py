"""Write a small synthetic dataset in CelebA layout, for smoke runs without real faces.

    python scripts/make_synthetic_data.py --out data/synthetic

Creates ``<out>/images/*.jpg`` and ``<out>/identity_synthetic.txt``, matching
``configs/smoke.json``. Then:

    python -m mini_ever make-split --config configs/smoke.json
    python -m mini_ever run exp00 --config configs/smoke.json --no-crop
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mini_ever.data.synthetic import SyntheticFaceLoader, synthetic_identity_images


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="data/synthetic")
    parser.add_argument("--identities", type=int, default=48)
    parser.add_argument("--min-images", type=int, default=20)
    parser.add_argument("--max-images", type=int, default=26)
    parser.add_argument("--size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    groups = synthetic_identity_images(args.identities, (args.min_images, args.max_images), args.seed)
    identity_of = {image: identity for identity, images in groups.items() for image in images}
    loader = SyntheticFaceLoader(identity_of, size=args.size, seed=args.seed)

    with open(out / "identity_synthetic.txt", "w", encoding="utf-8") as handle:
        for image_id, identity in sorted(identity_of.items()):
            loader(image_id).save(out / "images" / image_id, quality=95)
            handle.write(f"{image_id} {identity}\n")
    print(f"wrote {len(identity_of)} images of {len(groups)} identities to {out}")


if __name__ == "__main__":
    main()
