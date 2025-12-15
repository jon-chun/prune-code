# Prune Code (`prune-code`)

Prune Code is a CLI utility that creates **filtered, context-optimized copies** of repositories for LLM consumption.
It is designed for **spec-driven development**, code review, audit packaging, and “minimum-necessary context” workflows.

## Features

- **Whitelist-only scope** (safe by default)
- **Tiered Priority Cascade** for predictable precedence
- **Safer blacklist mode** toggle via global `FLAG_SAFER_BLACKLIST` (default `True`)
- **Datetime-stamp veto**: skip filenames containing a valid `YYYYMMDD` substring
- **Substring veto**: skip filenames containing configured tokens (case-insensitive)
- **Data sampling** for CSV/TSV/JSON/JSONL (head + tail)
- **Atomic writes** (temp file then replace)
- **CI-friendly overwrite modes**: prompt/force/fail
- **Verbose logging + skip reason breakdown**

## Install

```bash
uv pip install -e .
```

## Run

```bash
prune-code ./SOURCE ./DEST --dry-run --verbose
prune-code ./SOURCE ./DEST
```

Alternative:

```bash
python -m prune_code ./SOURCE ./DEST --dry-run --verbose
```

## CLI

```bash
prune-code SOURCE_DIR DEST_DIR \
  [--config PATH] [--dry-run] [--verbose] [--log-dir PATH] \
  [--overwrite {prompt,force,fail}] \
  [--safer-blacklist | --no-safer-blacklist]
```

## Precedence model

`FLAG_SAFER_BLACKLIST=True` (default):
1. **Tier 2 veto**: blacklist.files / blacklist.patterns / YYYYMMDD / substring tokens
2. **Tier 1 include**: whitelist.files (Golden Ticket)
3. **Tier 3 scope**: must be inside whitelist.directories
4. **Tier 4 sanity**: blacklist.directories / blacklist.extensions / max_file_size_mb

If `FLAG_SAFER_BLACKLIST=False`, Tier 1 and Tier 2 swap order.

## Tests

```bash
uv run pytest
```

## License
MIT. See `LICENSE`.
