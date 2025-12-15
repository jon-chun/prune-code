# Technical Specification (Maintainers)

This document describes prune-code internals for maintainers and future feature work.

## Module layout
- `prune_code.cli`: CLI parsing and invocation
- `prune_code.config`: YAML schema parsing and normalization
- `prune_code.distiller`: traversal + tiered decision engine
- `prune_code.sampling`: sampling implementations
- `prune_code.logging_utils`: console/file logging setup

## Tier engine invariants
- Paths are resolved (`Path.resolve()`) before relative computations.
- Decisions are deterministic for a given tree + config.
- All skips should record a tiered reason string for summary aggregation.

## Filename substring veto design
A naive substring approach (`"OLD" in filename.upper()`) creates false positives (e.g., `GOLD`).
The implementation uses tokenization of the filename stem and matches configured vetoes against tokens.

## Sampling design
- CSV/TSV: streaming head collection + bounded tail buffer; writes separator line with omitted count
- JSONL: line-based streaming head/tail (does not parse JSON objects)
- JSON: if top-level array, sample head/tail; otherwise copy intact

## Atomic writes
Sampling and copy operations should write to a temporary file and `replace()` into place to avoid partial outputs.

## Test strategy
- Unit tests for matching semantics and precedence toggles
- Integration tests running distill on a temp directory
- Regression tests for known edge cases (e.g., OLD vs GOLD)
