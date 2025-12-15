# prune-code technical specification

This document is intended for maintainers and future contributors. It explains the internal architecture, invariants,
and design decisions that enable `prune-code` to remain deterministic, auditable, and safe for “context distillation”.

---

## 1. Goals and non-goals

### Goals
- Produce a **filtered copy** of a source repository optimized for AI coding context ingestion.
- Provide a **deterministic, explainable** inclusion/exclusion decision for every visited file.
- Support a **whitelist-first scope model** suitable for security- and noise-sensitive workflows.
- Reduce size for common data formats via **sampling** while preserving schema-relevant context (head/tail).

### Non-goals
- Full `.gitignore` semantics replication (may be added later, but not required for correctness).
- Content-aware secret scanning (regex blacklists are supported; secret scanning is a distinct product area).
- Repository “understanding” or semantic summarization (this is a filtering/sampling utility, not an LLM itself).

---

## 2. Package layout (PyPI best practice)

The project uses a **src-layout**:

```text
src/prune_code/
  __init__.py
  __main__.py
  cli.py
  config.py
  distiller.py
  sampling.py
  logging_utils.py
```

Rationale:
- Prevents accidental imports from the project root during development.
- Aligns with modern Python packaging guidance and avoids path ambiguity.

Entrypoints:
- `python -m prune_code ...` via `__main__.py`
- `prune-code ...` via `project.scripts` in `pyproject.toml`

---

## 3. Configuration model

`config.yaml` is parsed into an immutable configuration object (`DistillerConfig`) that:
- normalizes extension lists
- compiles regex patterns
- configures token-based filename veto matching
- configures sampling parameters
- configures overwrite behavior

### 3.1 YAML rules
- Prefer **single quotes** for regex patterns to avoid YAML escape pitfalls.
- Globs are treated as repository-relative patterns (matched against normalized relative paths).

---

## 4. Decision engine: Tiered Priority Cascade

The core logic lives in `distiller.py` and is exposed via `RepositoryPruner.determine_action()`.

### 4.1 Terminology
- **Scope**: the set of candidate files defined by whitelist rules.
- **Veto**: a rule that forces a file to be skipped.
- **Sanity checks**: broad exclusions applied only after a file is in scope.

### 4.2 Tiers (conceptual)
1. Tier 1: explicit include (`whitelist.files`)
2. Tier 2: explicit veto (`blacklist.files`, `blacklist.patterns`, `blacklist.filename_substrings`, datetime stamps)
3. Tier 3: scope gate (`whitelist.directories`)
4. Tier 4: sanity exclusions (`blacklist.directories`, `blacklist.extensions`, size limit)

### 4.3 Safer blacklist precedence toggle
A global (and CLI-controlled) switch is supported:

- `FLAG_SAFER_BLACKLIST=True`: Tier 2 veto wins over Tier 1 include
- `FLAG_SAFER_BLACKLIST=False`: Tier 1 include wins over Tier 2 veto

This exists because there are two valid operational philosophies:
- **security/noise control** (veto wins)
- **explicit include as golden ticket** (include wins)

The default is safer veto-wins to reduce accidental inclusion of sensitive/noisy files.

---

## 5. Pattern matching semantics

### 5.1 Glob matching
- Patterns are normalized (leading `./` removed, trailing `/` trimmed where appropriate).
- Matching is performed against repository-relative paths.
- Directory patterns behave as prefix matches (a whitelisted directory includes descendants).
- Special-case: `"."` or empty directory pattern is treated as “match root scope”.

### 5.2 Regex matching
- Regex patterns are compiled at config load time.
- Regex is applied to **the filename (basename)** unless explicitly implemented otherwise.
- When contributors modify this behavior, update tests to reflect the target string (`path.name` vs relative path).

### 5.3 Filename substring veto (token-based)
Motivation: naive substring matching produces false positives (e.g., `OLD` matching `GOLD`).

Implementation principle:
- Convert filename stem (without extension) to tokens split on non-alphanumeric separators.
- Compare configured veto words case-insensitively against tokens.
- Only veto on token equality.

---

## 6. Data sampling subsystem

Sampling is implemented in `sampling.py` and invoked by the distiller when:
- sampling is enabled, and
- file extension is in `data_sampling.target_extensions`

### 6.1 CSV/TSV
- Stream reading: do not load entire file into memory.
- Preserve header (optional).
- Preserve first N data rows.
- Preserve last M data rows using a bounded deque.
- Emit a human-readable “omitted rows” marker.

### 6.2 JSONL
- Stream lines; preserve first N non-empty lines and last M non-empty lines.
- Do not parse JSON; treat each non-empty line as an object record.
- Emit an “omitted objects” marker.

### 6.3 JSON arrays
- Parse full JSON (tradeoff: may be memory-heavy; acceptable for moderate files).
- If top-level is a list, emit a sampled structure:
  - `_sampled`, `_total_items`, `_omitted_items`, `head`, `tail`
- If top-level is an object/primitive, copy intact.

### 6.4 Atomic writes
Sampling writes to a temporary file in the destination directory and replaces the final path atomically.
This prevents partial/corrupt outputs if interrupted.

---

## 7. Distillation workflow

High-level algorithm:
1. Resolve input paths to absolute paths.
2. Traverse `source_dir` using `rglob`.
3. For each file:
   - compute repository-relative path
   - determine action via cascade
   - if copy/sample: materialize destination parent dirs and write atomically
4. Emit summary:
   - totals (scanned, copied, sampled, skipped, errors)
   - skip reasons breakdown for auditability

---

## 8. Error handling and resilience

Principles:
- Fail-soft on per-file errors: increment `errors`, log, continue.
- Fail-hard on invalid config load (cannot proceed safely).
- Use robust encoding handling (`errors="replace"`) for text sampling.
- Prefer atomic writes.

Recommended future hardening:
- explicit symlink policy
- optional “stop on first error” mode
- optional structured (JSON) log output

---

## 9. Testing strategy

Tests should cover:
- tier precedence including safer toggle behavior
- token-based substring veto regression (`GOLD` vs `OLD`)
- datetime stamp detection validity
- sampling correctness for CSV/JSONL/JSON arrays
- overwrite behaviors (`force`, `fail`, `prompt`)
- permission/unreadable file behavior (skip or error as designed)

---

## 10. Extension points

Common requested features:
- `.gitignore` parsing support (as optional additional veto layer)
- allowlist/denylist per extension per directory
- “profile” configs for different AI workflows (chat vs IDE vs agentic)
- integration with repomix-like downstream packagers

When adding features, maintain:
- deterministic rule ordering
- explicit tests for each precedence interaction
- clear documentation and examples in the user manual
