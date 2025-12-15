# Configuration

prune-code reads a YAML file (default: `./config.yaml`).

## Minimal schema

```yaml
max_file_size_mb: 5
overwrite_mode: "prompt"

whitelist:
  files: []
  directories: []

blacklist:
  files: []
  extensions: []
  patterns: []
  directories: []
  datetime_stamp_yyyymmdd: true
  filename_substrings: ["BACKUP", "OLD"]

data_sampling:
  enabled: true
  target_extensions: [".csv", ".jsonl"]
  include_header: true
  head_rows: 5
  tail_rows: 5
```

## Whitelisting

### whitelist.files
Use for “golden ticket” inclusions that should be considered even if most directories are out-of-scope.

Example:

```yaml
whitelist:
  files:
    - "src/step5_qa-gold-dataset.py"
```

### whitelist.directories
Defines the “scope” of what can be included.

Example:

```yaml
whitelist:
  directories:
    - "src/qa_gold_lib/"
    - "tests/"
```

## Blacklisting

### blacklist.patterns (regex)
Patterns are evaluated against the **filename** (not the full path).

!!! tip "YAML quoting"
    Use single quotes for regex patterns to avoid escaping surprises:
    `'_v\d{1,2}\.py$'`

### “Keep only one step5 script” recipe

```yaml
blacklist:
  patterns:
    - '^step[1-4]'
    - '^step5_.*_v\d{1,2}\.py$'
    - '_v\d{1,2}\.py$'
```

### blacklist.filename_substrings (token-based)
These are **tokens** matched against the filename stem. Tokens are formed by splitting on separators like `-` and `_`.

This avoids the classic pitfall:

- `OLD` should not match `GOLD`
- but should match `*_OLD_*`

### blacklist.datetime_stamp_yyyymmdd
When enabled, any filename containing a valid date stamp (e.g., `20251215`) will be vetoed.

## Data sampling
Sampling only applies to files that would otherwise be copied, and only for the configured extensions.

Example for CSV/JSONL:

```yaml
data_sampling:
  enabled: true
  target_extensions: [".csv", ".jsonl"]
  include_header: true
  head_rows: 5
  tail_rows: 5
```
