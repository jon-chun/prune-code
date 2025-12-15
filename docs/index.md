# prune-code

prune-code distills a repository into a smaller, high-signal copy intended for LLM context engineering and AI-assisted software development.

!!! tip "Recommended workflow"
    Start with a dry run, inspect skip reasons, then iterate on `config.yaml` until the output is correct.

## Quick start

```bash
prune-code ./SOURCE ./DEST --dry-run --verbose
```

Once the preview looks correct:

```bash
prune-code ./SOURCE ./DEST --overwrite force
```

## Core concepts

- **Whitelist-first**: only explicitly whitelisted files or files inside whitelisted directories are eligible.
- **Tiered priority cascade**: a deterministic, explainable set of rules decides COPY/SAMPLE/SKIP.
- **Sampling**: for large structured datasets, keep head + tail samples to reduce token usage.
- **Auditability**: every skip has a tier + reason; summaries provide counts by reason.

## Where to go next
- Installation: see **Installation**
- Configure rules: see **Configuration**
- Troubleshoot: see **Edge Cases & FAQ**
