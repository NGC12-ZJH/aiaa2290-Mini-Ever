"""Command-line interface: ``python -m mini_ever <command> ...``.

Commands
--------
check-config  Validate a config and list the research decisions still open.
make-split    Build the split manifest from the CelebA identity file.
train         Train (or load from cache) the public base or the main models.
run           Run one experiment (exp00 ... exp04).

Every command takes ``--config``; ``run`` and ``train`` refuse to start while
the config still has ``null`` decisions (see docs/protocol.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from mini_ever.config import ConfigIncompleteError, load_config
from mini_ever.data.celeba import group_by_identity, read_identity_file
from mini_ever.data.splits import SplitManifest, build_split


def _cmd_check_config(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    missing = config.missing_fields()
    print(f"config: {args.config}")
    print(f"status: {config.status}")
    print(f"sha256: {config.hash()}")
    if missing:
        print("still open (must be fixed before a run):")
        for name in missing:
            print(f"  - {name}")
        return 1
    print("all research decisions are fixed")
    return 0


def _cmd_make_split(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out = Path(config.data.manifest_path)
    if out.exists() and not args.force:
        print(f"{out} exists; pass --force to rebuild it (this changes every cache key)", file=sys.stderr)
        return 1
    identity_file = Path(config.data.local_root) / config.data.identity_file
    manifest = build_split(group_by_identity(read_identity_file(identity_file)), config.data)
    manifest.save(out)
    print(json.dumps(manifest.summary(), indent=2))
    print(f"manifest written to {out} (local only - do not commit)")
    return 0


def _context(args: argparse.Namespace):
    from mini_ever.context import Context

    config = load_config(args.config)
    kwargs = {"device": args.device}
    if getattr(args, "no_crop", False):
        kwargs["crop_box"] = None
    return Context.from_config(config, **kwargs)


def _cmd_train(args: argparse.Namespace) -> int:
    ctx = _context(args)
    if args.what == "public-base":
        ctx.public_base()
        print(f"public base ready: {ctx.artifact_id(ctx.public_base())}")
    else:
        for seed in args.seeds or ctx.seeds:
            model = ctx.main_model(seed)
            print(f"main model (seed {seed}) ready: {ctx.artifact_id(model)}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    from mini_ever.experiments import EXPERIMENTS

    ctx = _context(args)
    options = {"groups": args.groups, "seeds": args.seeds}
    if args.methods:
        options["methods"] = args.methods
    result = EXPERIMENTS[args.experiment].run(ctx, **options)
    print(json.dumps(result, indent=2, ensure_ascii=False)[: args.print_chars])
    print(f"\nfull result written under {ctx.results_dir / EXPERIMENTS[args.experiment].NAME}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini_ever", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", required=True, help="path to the JSON config")

    def runtime(p: argparse.ArgumentParser) -> None:
        p.add_argument("--device", default=None, help="cuda, cuda:0 or cpu (default: auto)")
        p.add_argument("--seeds", type=int, nargs="*", default=None, help="subset of training seeds")
        p.add_argument("--no-crop", action="store_true", help="skip the CelebA face crop (synthetic data)")

    p = sub.add_parser("check-config", help="validate a config and list open decisions")
    common(p)
    p.set_defaults(func=_cmd_check_config)

    p = sub.add_parser("make-split", help="build the split manifest")
    common(p)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=_cmd_make_split)

    p = sub.add_parser("train", help="train or load cached models")
    common(p)
    runtime(p)
    p.add_argument("what", choices=["public-base", "main"])
    p.set_defaults(func=_cmd_train)

    p = sub.add_parser("run", help="run an experiment")
    common(p)
    runtime(p)
    p.add_argument("experiment", choices=["exp00", "exp01", "exp02", "exp03", "exp04"])
    p.add_argument("--groups", type=int, nargs="*", default=None, help="subset of forget groups")
    p.add_argument("--methods", nargs="*", default=None, help="exp03 only: subset of methods")
    p.add_argument("--print-chars", type=int, default=4000, help="how much of the result to print")
    p.set_defaults(func=_cmd_run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigIncompleteError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
