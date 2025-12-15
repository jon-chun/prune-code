# User Manual

This guide is for end-users running prune-code as a CLI to distill repositories.

## Basic usage

Dry run first:

```bash
prune-code SOURCE DEST --dry-run --verbose
```

Run for real:

```bash
prune-code SOURCE DEST --overwrite force
```

## Interpreting output

- `COPY` means the file is copied verbatim.
- `SAMPLE` means prune-code writes a reduced representation (CSV/TSV/JSON/JSONL only).
- `SKIP[tierX_reason]` indicates the tier and rule that excluded the file.

## Overwrite behavior

Use `--overwrite` to control destination handling:

- `prompt` (default): ask before deleting destination
- `force`: delete destination if it exists
- `fail`: exit non-zero if destination exists

Examples:

```bash
prune-code SOURCE DEST --overwrite fail
prune-code SOURCE DEST --overwrite force
```

## Precedence toggle (safer blacklist)

By default, prune-code uses safer semantics where blacklist vetoes override explicit whitelist files.

- Safer (default):
  ```bash
  prune-code SOURCE DEST --safer-blacklist
  ```
- Whitelist wins:
  ```bash
  prune-code SOURCE DEST --no-safer-blacklist
  ```

!!! warning "Security note"
    If your repositories may contain secrets, keep `--safer-blacklist` enabled and explicitly blacklist sensitive patterns and files.

## Sampling

Sampling is intended for token reduction for LLM context.

Supported:
- `.csv`, `.tsv`: header (optional) + head rows + tail rows
- `.jsonl`: head lines + tail lines (line-based; does not parse JSON objects)
- `.json`: if top-level is an array, sample head + tail items; objects are copied intact

See **Configuration** for the exact knobs.
