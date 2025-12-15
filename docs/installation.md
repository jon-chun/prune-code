# Installation

This project supports Python 3.8+ and is tested through Python 3.12.

## Option A: Install with pip

```bash
pip install prune-code
```

## Option B: Install with uv (recommended)

Create a dedicated virtual environment and install:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install prune-code
```

## Development install (contributors)

```bash
git clone https://github.com/jon-chun/prune-code
cd prune-code
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,docs]"
pytest
mkdocs serve
```

!!! note "Why docs are optional dependencies"
    The `docs` toolchain (MkDocs Material + mkdocstrings) is intentionally in `.[docs]` so that end-users only install runtime dependencies.
