# Prune Code — User Manual

## Install
```bash
uv pip install -e .
```

## Typical workflow
1) Configure scope in `config.yaml` (directories first, then files)
2) Run a dry run to validate decisions
3) Run for real
4) Inspect logs and skip reason breakdown
5) Iterate config

## Commands
Dry run:
```bash
prune-code ./SOURCE ./DEST --dry-run --verbose
```

Real run:
```bash
prune-code ./SOURCE ./DEST --overwrite prompt
```

CI-safe:
```bash
prune-code ./SOURCE ./DEST --overwrite fail
```

## Cookbook for edge cases

### 1. Tier 1 include behavior
- Add a file to `whitelist.files` that would otherwise be excluded (e.g. inside `node_modules/`)
- Confirm it is copied/sampled.

### 2. Tier 2 veto behavior
- Add `secrets.py` to `blacklist.files`
- Add regex patterns for sensitive content names
- Confirm they are skipped even if in scope.

### 3. Datestamp veto
- Create `report_20251207.txt` -> should skip (valid date)
- Create `report_20251340.txt` -> should not skip based on date stamp rule

### 4. Substring veto (case-insensitive)
- Create `notes_backup.txt` -> should skip

### 5. Bad data
- Invalid JSON: should be copied intact, not crash
- UTF-8 errors: handled using replacement

### 6. Large repos
- Start with narrow scope directories
- Expand scope iteratively
- Use `--verbose` plus log file for auditing

