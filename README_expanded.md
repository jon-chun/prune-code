# prune-code

**prune-code** is a Python CLI and library for creating **filtered, context‑optimized copies** of a source repository.
It is designed for **LLM-friendly context engineering**: shrinking messy repos into a deterministic, auditable subset
that is cheap to index, feed to AI coding tools, or pass into downstream distillers (e.g., repomix-like workflows).

It uses a **whitelist-first “scope” model** with a **tiered priority cascade** and optional **data sampling**
(head + tail) for large structured files.

---

## Why this exists

Real repositories often contain:
- large datasets, exports, and logs
- build artifacts and virtualenvs
- vendor trees and `node_modules/`
- iterative script versions (`*_v7.py`, “backup”, “old”, dated exports)

Those files are high-noise and high-token-cost for LLM consumption. `prune-code` produces a clean “distilled” repo
that keeps only what you intend, with traceable decisions and repeatable results.

---

## Key features

- **Whitelist-first filtering**: if it isn’t explicitly in scope, it’s excluded.
- **Tiered precedence** (explainable and testable).
- **“Safer blacklist” toggle** to decide whether veto rules override explicit includes.
- **Token-based filename vetoes** (prevents false positives like `OLD` matching `GOLD`).
- **Datetime-stamp veto** for filenames containing `YYYYMMDD` dates (optional).
- **Data sampling** for `.csv/.tsv/.json/.jsonl` to preserve head + tail while dropping bulk.
- **Dry run mode** to preview actions without writing.
- **Detailed logs + skip reason breakdown** for auditability.
- **Atomic writes** to avoid partial/corrupt outputs if interrupted.

---

## Installation

### From PyPI
```bash
pip install prune-code
```

### For development (editable install)
```bash
git clone https://github.com/jon-chun/prune-code
cd prune-code
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Quick start

### 1) Create or edit `config.yaml`
Start from the included `config.yaml` at the repo root.

### 2) Run a dry run
```bash
prune-code /path/to/source-repo /path/to/distilled-repo --dry-run --verbose -c config.yaml
```

### 3) Run for real
```bash
prune-code /path/to/source-repo /path/to/distilled-repo --overwrite force --verbose -c config.yaml
```

---

## How the filtering works

`prune-code` evaluates each file using a **Tiered Priority Cascade**.

### Tier overview

1. **Tier 1 — Explicit include (`whitelist.files`)**
   - Exact or glob match for specific files.
2. **Tier 2 — Explicit veto (`blacklist.files`, `blacklist.patterns`, `blacklist.filename_substrings`, datetime stamp)**
   - Strong “do not include” rules.
3. **Tier 3 — Scope gate (`whitelist.directories`)**
   - If a file is not in a whitelisted directory and not explicitly whitelisted, it is out of scope.
4. **Tier 4 — General exclusions (directory blacklist, extension blacklist, size limit)**
   - Sanity checks for files that are in scope.

### The `FLAG_SAFER_BLACKLIST` toggle

`prune-code` exposes a global default and CLI flags to control whether Tier 2 veto rules override Tier 1 includes.

- **Default:** `FLAG_SAFER_BLACKLIST=True`  
  Tier 2 veto **wins** over Tier 1 include (security/noise control).
- If set to **False**, Tier 1 include **wins** over Tier 2 veto (more “golden ticket” behavior).

CLI:
```bash
# Force safer behavior (Tier 2 > Tier 1)
prune-code ... --safer-blacklist

# Allow “golden ticket” behavior (Tier 1 > Tier 2)
prune-code ... --no-safer-blacklist
```

**Recommendation:** keep the default safer behavior for shared/team configs; use `--no-safer-blacklist` when you
intentionally want explicit includes to bypass vetoes.

---

## Configuration guide

`config.yaml` is divided into four conceptual areas:

- **Whitelist**: defines *scope* (what can be considered)
- **Blacklist**: defines *vetoes* and *exclusions*
- **Sampling**: reduces size of structured data
- **Operational**: environment labels, overwrite behavior, verbosity

### Whitelist

```yaml
whitelist:
  files:
    - "README.md"
    - "src/step5_qa-gold-dataset.py"
  directories:
    - "src/"
    - "tests/"
```

- Use `files` for surgical includes.
- Use `directories` for “include everything under here unless excluded.”

### Blacklist

#### Regex patterns (filename-level)
Patterns are matched against the **basename** by default. Use **single quotes** to avoid YAML escaping issues:

```yaml
blacklist:
  patterns:
    - '^step[1-4]'
    - '^step5_.*_v\d{1,2}\.py$'
    - '_v\d{1,2}\.py$'
```

#### Filename substrings (token-based, case-insensitive)
```yaml
blacklist:
  filename_substrings: ["BACKUP", "OLD", "FINAL"]
```

These are matched against **tokens** derived from the filename stem (split on `- _ . space` and other separators).
This prevents false positives such as:

- `GOLD` accidentally matching `OLD` (because token ≠ substring-in-word).

#### Datetime-stamp veto (`YYYYMMDD`)
```yaml
blacklist:
  datetime_stamp_yyyymmdd: true
```

If enabled, any filename containing a valid calendar date in `YYYYMMDD` form is vetoed.

### Data sampling

```yaml
data_sampling:
  enabled: true
  target_extensions: [".csv", ".tsv", ".json", ".jsonl"]
  include_header: true
  head_rows: 5
  tail_rows: 5
```

Sampling behavior:
- CSV/TSV: header (optional) + first N rows + last M rows + “omitted rows” marker
- JSONL: first N lines + last M lines + “omitted objects” marker (streamed)
- JSON arrays: outputs a sampled structure with metadata + head/tail
- JSON objects/primitives: copied intact

---

## Logging and troubleshooting

### Where logs go
By default logs are written under `./logs/` (configurable via CLI). Console output is concise; the log file includes
debug-level trace of decisions.

### Common troubleshooting patterns

#### “My explicitly whitelisted file is still skipped”
- Check whether a **Tier 2 veto** is firing (patterns, filename_substrings, datetime stamp).
- Grep for the filename in the log:
  ```bash
  grep -n "your-file-name" logs/log_*.txt | tail -n 20
  ```

#### Edge case: substring veto false positives
If you configure `filename_substrings: ["OLD"]` and see unexpected skips, ensure you are on a version that uses
**token-based** matching (v2.0.2+). This prevents `GOLD` from matching `OLD`.

---

## Development

### Run tests
```bash
pytest
```

### Linting / typing (optional)
If you add tooling later (ruff, mypy), keep it behind optional `.[dev]` extras.

---

## License
MIT. See `LICENSE`.
