#!/usr/bin/env bash
# Download CelebA (aligned images + identity labels) from the flwrlabs/celeba
# copy on hf-mirror.com and verify each shard against its LFS SHA-256.
#
# The official Google Drive links failed (gdown) on both of our machines, and
# the GPU server cannot reach Google Drive or huggingface.co. CelebA is
# licensed for non-commercial research only.
#
# Usage: bash scripts/download_celeba_mirror.sh [raw_dir]   (default ~/celeba_raw)
# Re-running resumes partial files. 25 shards, 11.7 GB in total.
set -u
RAW=${1:-$HOME/celeba_raw}
mkdir -p "$RAW" && cd "$RAW" || exit 1
export BASE=https://hf-mirror.com/datasets/flwrlabs/celeba/resolve/main/img_align%2Bidentity%2Battr
TREE=https://hf-mirror.com/api/datasets/flwrlabs/celeba/tree/main/img_align%2Bidentity%2Battr

one() {
  f=$1
  [ -s "$f.done" ] && return
  for _ in 1 2 3 4 5 6; do
    curl -sSL -C - -o "$f" "$BASE/$f" && { echo ok > "$f.done"; echo "got $f"; return; }
    sleep 5
  done
  echo "FAILED $f"
}
export -f one

# One connection is ~0.6 MB/s; 8 in parallel reached 3-10 MB/s. A connection
# that stalls (tens of KB/s) can be killed: the loop resumes it with -C -.
{ seq -f "train-%05g-of-00019.parquet" 0 18
  seq -f "valid-%05g-of-00003.parquet" 0 2
  seq -f "test-%05g-of-00003.parquet" 0 2; } | xargs -P 8 -I{} bash -c 'one {}'

curl -s "$TREE" | python3 -c '
import json, sys
for x in json.load(sys.stdin):
    print(x["lfs"]["oid"] + "  " + x["path"].split("/")[-1])' > expected.sha256
sha256sum -c expected.sha256 --quiet && echo "ALL_DONE: all shards verified"
