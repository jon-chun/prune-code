# prune-code user manual

This guide is for end users who want a reliable way to “distill” a repository into a smaller, AI-friendly subset.

---

## 1. What prune-code does

Given:

- a **source repo** (often messy, large, or noisy)
- a **destination directory**
- a **config.yaml** describing what is in scope and what is vetoed

`prune-code` walks the source repository and produces a filtered copy at the destination.
For large structured data, it can sample head/tail to reduce size while preserving context.

---

## 2. Installation

```bash
pip install prune-code
```

Verify:
```bash
prune-code --help
python -m prune_code --help
```

---

## 3. Basic usage

### Dry run (recommended first)
```bash
prune-code ./source ./dest --dry-run --verbose -c config.yaml
```

### Real run
```bash
prune-code ./source ./dest --overwrite force --verbose -c config.yaml
```

Overwrite modes:
- `prompt` (default): ask before deleting an existing destination
- `force`: delete destination without prompting
- `fail`: abort if destination exists (best for CI)

---

## 4. Understanding the filtering model

`prune-code` uses a **whitelist-first** approach.

If a file is not explicitly in scope, it is skipped.

### Rule tiers
1. **Whitelist files**: exact/glob includes
2. **Blacklist veto**: explicit “never include” rules
3. **Whitelist directories**: defines the broad scope
4. **Sanity exclusions**: extensions, size cap, blacklisted subdirectories

### Safer blacklist precedence
There are two valid philosophies:

- **Safer (default):** veto wins over include  
  Prevents accidental inclusion of sensitive/noisy files.
- **Golden ticket:** include wins over veto  
  If you explicitly whitelisted it, you always get it.

Control via CLI:
```bash
prune-code ... --safer-blacklist
prune-code ... --no-safer-blacklist
```

---

## 5. Config reference with examples

### 5.1 Minimal “code-only” distill
```yaml
whitelist:
  directories:
    - "src/"
    - "tests/"

blacklist:
  directories:
    - ".git/"
    - ".venv/"
    - "node_modules/"
  extensions:
    - ".png"
    - ".pdf"
```

### 5.2 “Include one file, exclude the rest”
To include a single script but exclude other step files:

```yaml
whitelist:
  files:
    - "src/step5_qa-gold-dataset.py"
  directories:
    - "src/"
blacklist:
  patterns:
    - '^step[1-4]'
    - '^step5_.*_v\d{1,2}\.py$'
```

### 5.3 Excluding dated exports
```yaml
blacklist:
  datetime_stamp_yyyymmdd: true
```
This vetoes filenames that contain valid dates like `20251215`.

### 5.4 Excluding backups and variants (token-based)
```yaml
blacklist:
  filename_substrings: ["BACKUP", "OLD", "FINAL"]
```

Important: token-based matching prevents false positives. Example:
- `step5_qa-gold-dataset.py` contains `gold` but **does not** match token `OLD`.

---

## 6. Sampling large data files

Enable sampling:
```yaml
data_sampling:
  enabled: true
  target_extensions: [".csv", ".jsonl"]
  head_rows: 5
  tail_rows: 5
```

When sampling triggers:
- The file is in scope (whitelist) and not vetoed.
- The extension matches `target_extensions`.

Sampling output includes a visible “omitted rows/objects” marker.

---

## 7. Reading logs and debugging decisions

### 7.1 Locate the log file
The tool prints the log path on startup. Logs are created under `./logs/` by default.

### 7.2 Debug a specific file
Search for the file path:
```bash
grep -n "src/step5_qa-gold-dataset.py" logs/log_*.txt | tail -n 20
```

You will see decisions like:
- `COPY: ...`
- `SAMPLE: ...`
- `SKIP[tier2_blacklist_pattern:...]: ...`

### 7.3 Common issues

#### “My file is whitelisted but still skipped”
Most often:
- A Tier 2 veto is firing (pattern, filename substrings, datetime stamp).
- You are using safer precedence (Tier 2 > Tier 1).

Fix:
- adjust the veto rule, or
- run with `--no-safer-blacklist` if that matches your intent.

#### “Nothing was created at the destination”
Check whether you ran with `--dry-run`.
Dry runs do not write or create the destination directory.

#### “Sampling didn’t happen”
Likely causes:
- file was out of scope (Tier 3)
- file was vetoed (Tier 2)
- extension not in `data_sampling.target_extensions`

---

## 8. Cookbook: building configs safely

1. Start with a strict scope:
   - whitelist only `src/` and `tests/`
2. Run dry-run and confirm counts.
3. Add explicit whitelist files for must-have artifacts.
4. Add veto rules for secrets/noise.
5. Enable sampling once scope is correct.
6. Pin overwrite mode (`fail` in CI, `force` locally).

---

## 9. FAQ

**Q: Does prune-code respect `.gitignore`?**  
Not by default. You can approximate behavior using blacklist rules. `.gitignore` support is a reasonable future enhancement.

**Q: Can it follow symlinks?**  
Current behavior is OS/filesystem dependent. If you need deterministic symlink behavior, request explicit symlink policy support.

**Q: Is this safe for sensitive repos?**  
Use safer precedence, keep strong veto rules for secrets, and validate logs. For true secret prevention, pair with secret-scanning workflows.

---

## 10. Getting help
If something looks wrong, capture:
- command line used (including `-c`)
- the relevant `config.yaml`
- `grep` output for the file in question from the log
- the summary “skip reasons breakdown”
