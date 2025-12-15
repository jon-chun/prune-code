# prune-code

[![PyPI](https://img.shields.io/pypi/v/prune-code)](https://pypi.org/project/prune-code/)
[![Python Versions](https://img.shields.io/pypi/pyversions/prune-code)](https://pypi.org/project/prune-code/)
[![License: MIT](https://img.shields.io/github/license/jon-chun/prune-code)](https://github.com/jon-chun/prune-code/blob/main/LICENSE)

prune-code is a Python CLI and library that creates **filtered, context-optimized copies of repositories** for
LLM-friendly context engineering.

It is designed for situations where you need to feed a repository into an AI coding workflow and want:
- strict control over what files are included,
- deterministic, explainable filtering decisions,
- smaller, sampled versions of large data files (CSV/JSON/JSONL),
- a clean “distilled” tree you can hand to other tools (e.g., repomix) or directly to an LLM.

## What problem does it solve?

Real repositories usually contain noise:
- caches (`.venv/`, `__pycache__/`, `node_modules/`),
- artifacts (`dist/`, `build/`, logs, exports),
- versioned files (`*_v1.py`, `*_v2.py`),
- backups (`BACKUP`, `OLD`, `ORIGINAL`),
- huge datasets that exceed token budgets.

prune-code helps you keep the **signal** and drop the **noise**, while producing a copy you can safely share, audit,
and iterate on.

## How it works: Tiered Priority Cascade

Filtering is done via `config.yaml` using a tiered decision model:

1. **Tier 1 – Explicit whitelist files** (`whitelist.files`)
2. **Tier 2 – Explicit veto** (`blacklist.files`, `blacklist.patterns`, date-stamps, and filename tokens)
3. **Tier 3 – Whitelist directory scope** (`whitelist.directories`)
4. **Tier 4 – Sanity checks** (`blacklist.directories`, `blacklist.extensions`, `max_file_size_mb`)

### Safer blacklist toggle

Some teams want “explicit blacklist always wins” (safer for secrets). Others want “explicit whitelist file is a golden ticket” (more intuitive).

prune-code supports both via a toggle:

- Default: `FLAG_SAFER_BLACKLIST=True` (Tier 2 veto overrides Tier 1)
- Override per-run:
  - `--safer-blacklist` (Tier 2 > Tier 1)
  - `--no-safer-blacklist` (Tier 1 > Tier 2)

## Installation

### From PyPI

```bash
pip install prune-code
# or
uv pip install prune-code
```

### Development install

```bash
git clone https://github.com/jon-chun/prune-code
cd prune-code
uv pip install -e ".[dev,docs]"
```

## Quick start

Dry-run first (recommended):

```bash
prune-code ./source-repo ./distilled-repo --dry-run --verbose
```

Then run for real:

```bash
prune-code ./source-repo ./distilled-repo --overwrite force
```

## Configuration: practical examples

### Copy a specific “must-include” file even when excluding most directories

```yaml
whitelist:
  files:
    - "src/step5_qa-gold-dataset.py"
  directories:
    - "src/qa_gold_lib/"
    - "tests/"
```

### Filter `src/step*` files but keep a single target

Common pattern: exclude `step1..step4`, exclude `step5_*_vN.py`, but keep `step5_qa-gold-dataset.py`:

```yaml
blacklist:
  patterns:
    - '^step[1-4]'
    - '^step5_.*_v\d{1,2}\.py$'
    - '_v\d{1,2}\.py$'
```

### Avoid the “OLD vs GOLD” pitfall

If you blacklist the token `OLD`, a naive substring check would accidentally block files containing `GOLD`.
prune-code implements **token-based** matching by default (splitting filename stems on separators) so that:
- `...-GOLD-...` does not match token `OLD`
- `..._OLD_...` does match token `OLD`

## Logging, tracing, and debugging

- Console output is concise; file logs contain full detail.
- Logs are written to `./logs/` (created automatically if missing).

Recommended workflow:
1. Run `--dry-run --verbose`
2. Search the log for a specific file decision:
   ```bash
   grep -n "relative/path/to/file" logs/log_*.txt | tail -n 20
   ```
3. Tune `config.yaml` and repeat.

## Documentation

- User manual: `docs/user-manual.md`
- Configuration reference: `docs/configuration.md`
- Edge cases & FAQ: `docs/edge-cases.md`
- Technical spec (maintainers): `docs/tech-specs.md`

To serve docs locally:

```bash
uv pip install -e ".[docs]"
mkdocs serve
```

## License
MIT. See `LICENSE`.
