# Prune Code — Technical Specification (v2.0.1)

## Overview
Prune Code produces a filtered, LLM-friendly copy of a repository using a whitelist-only posture plus
explicit blacklists and optional data sampling.

## Package layout
- `prune_code/cli.py`: argument parsing and entry point
- `prune_code/config.py`: YAML parsing and normalization
- `prune_code/distiller.py`: traversal, policy evaluation, file ops
- `prune_code/sampling.py`: CSV/TSV/JSON/JSONL sampling
- `prune_code/logging_utils.py`: logging setup
- `prune_code/__main__.py`: `python -m prune_code`

## Decision cascade
A file path is evaluated by tiers. Precedence is controlled by module global:

- `FLAG_SAFER_BLACKLIST=True`: Tier 2 veto runs before Tier 1 include
- `FLAG_SAFER_BLACKLIST=False`: Tier 1 include runs before Tier 2 veto

Tier definitions:
- Tier 1: explicit whitelist file match (`whitelist.files`) -> COPY or SAMPLE
- Tier 2: explicit vetoes (blacklist files / regex / date stamp / substrings) -> SKIP
- Tier 3: whitelist-only directory scope (`whitelist.directories`) -> SKIP if not in scope
- Tier 4: general exclusions (blacklist directories/extensions/size) -> SKIP

## Sampling
- CSV/TSV: stream read; keep header (optional) + head N + tail M; omission marker
- JSONL: stream non-empty lines; keep head/tail; omission marker
- JSON arrays: write sampled object with metadata and head/tail
- JSON objects/primitives: copied intact

## Reliability
- Per-file errors are trapped; stats increment; run continues
- Writes are atomic using temp files and `replace()`
- Destination overwrite is controlled via `overwrite_mode` and CLI `--overwrite`

