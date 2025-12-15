# Edge Cases & FAQ

## Dry run vs real run

| Symptom | Explanation | Fix |
|---|---|---|
| Summary shows “Files copied: N” but destination is empty/missing | Dry run simulates actions but does not write files | Remove `--dry-run` |
| Destination not created on dry run | Expected behavior | Run non-dry or create directory manually |

## “OLD” accidentally blocks “GOLD”

If you blacklist `OLD` and your project contains `GOLD` filenames, naive substring matching would skip files unexpectedly.
prune-code uses **token-based** vetoes so that `GOLD` does not match `OLD`.

!!! example
    - `examples_GOLD_unlabeled.csv` → tokens include `GOLD` (not `OLD`)
    - `examples_OLD_unlabeled.csv` → tokens include `OLD` (veto)

## Regex surprises

- Patterns are matched against **filenames**, not full paths.
- Prefer single quotes in YAML.
- Validate a specific file decision by grepping logs:

```bash
grep -n "step5_qa-gold-dataset.py" logs/log_*.txt | tail -n 20
```

## Why was my file skipped?

1. Check the tier and reason in logs.
2. Ensure you used the intended config file (`-c /absolute/path/to/config.yaml`).
3. If the file is explicitly whitelisted but vetoed, check:
   - `--safer-blacklist` mode
   - Tier 2 settings (patterns, tokens, date stamps)
