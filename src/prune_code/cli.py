from __future__ import annotations
import argparse
from pathlib import Path

from .config import DistillerConfig
import prune_code.distiller as dist
from .distiller import RepositoryDistiller
from .logging_utils import setup_logging

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog='prune-code',
        description='Prune Code: filter and sample a repository into an LLM-friendly distilled copy.'
    )
    p.add_argument('source_dir', type=Path)
    p.add_argument('destination_dir', type=Path)
    p.add_argument('-c', '--config', type=Path, default=Path('./config.yaml'))
    p.add_argument('-d', '--dry-run', action='store_true')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('--log-dir', type=Path, default=Path('./logs'))
    p.add_argument('--overwrite', choices=['prompt', 'force', 'fail'], default=None)
    p.add_argument('--safer-blacklist', dest='safer_blacklist', action='store_true', default=None)
    p.add_argument('--no-safer-blacklist', dest='safer_blacklist', action='store_false', default=None)
    p.add_argument('--version', action='version', version='prune-code 2.0.1')
    return p.parse_args()

def main() -> int:
    args = parse_args()
    logger = setup_logging(args.log_dir.resolve(), verbose=args.verbose)

    config = DistillerConfig.from_yaml(args.config.resolve(), logger=logger)

    if args.safer_blacklist is not None:
        dist.FLAG_SAFER_BLACKLIST = bool(args.safer_blacklist)

    d = RepositoryDistiller(config, logger)
    ok = d.distill(
        args.source_dir.resolve(),
        args.destination_dir.resolve(),
        dry_run=args.dry_run,
        overwrite_mode=args.overwrite,
    )
    return 0 if ok else 1
