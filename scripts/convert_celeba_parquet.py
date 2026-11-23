"""Turn the flwrlabs/celeba parquet shards into the layout Mini-Ever reads.

Output: ``<out>/img_align_celeba/*.png`` and ``<out>/identity_CelebA.txt``.

Image bytes are written unchanged (PNG, as stored in the mirror). File names come
from each row's original ``path`` field when present, else from a running index
in train -> valid -> test order. The mirror renumbers identities relative to the
official ``identity_CelebA.txt``, which does not matter here: identities are
anonymous integers either way.

Needs ``pyarrow``, which is not a project dependency. Install it into a separate
directory so the project environment stays unchanged::

    pip install --target ~/tools/pylib pyarrow
    PYTHONPATH=~/tools/pylib python scripts/convert_celeba_parquet.py ~/celeba_raw data/celeba
"""

import sys
from pathlib import Path

import pyarrow.parquet as pq

SHARDS = (
    [f"train-{i:05d}-of-00019.parquet" for i in range(19)]
    + [f"valid-{i:05d}-of-00003.parquet" for i in range(3)]
    + [f"test-{i:05d}-of-00003.parquet" for i in range(3)]
)


def main(raw: Path, out: Path) -> None:
    img_dir = out / "img_align_celeba"
    img_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    names: set[str] = set()
    idx = 0
    for name in SHARDS:
        for batch in pq.ParquetFile(raw / name).iter_batches(columns=["image", "celeb_id"], batch_size=2000):
            images = batch.column("image").to_pylist()
            ids = batch.column("celeb_id").to_pylist()
            for img, cid in zip(images, ids):
                idx += 1
                fname = f"{Path(img.get('path') or '').stem or f'{idx:06d}'}.png"
                assert fname not in names, f"duplicate file name {fname}"
                names.add(fname)
                (img_dir / fname).write_bytes(img["bytes"])
                lines.append(f"{fname} {int(cid)}\n")
        print(name, idx, flush=True)
    (out / "identity_CelebA.txt").write_text("".join(lines))
    print("images", idx, "identities", len({line.split()[1] for line in lines}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
