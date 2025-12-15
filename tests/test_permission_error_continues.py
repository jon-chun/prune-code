from __future__ import annotations
import os
import stat
from pathlib import Path
import pytest

from prune_code.config import DistillerConfig, WhitelistConfig, BlacklistConfig, DataSamplingConfig
from prune_code.distiller import RepositoryDistiller

class DummyLogger:
    def info(self, *a, **k): pass
    def debug(self, *a, **k): pass
    def error(self, *a, **k): pass

@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions test")
def test_unreadable_file_increments_errors_and_continues(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()

    good = src / "good.txt"
    bad = src / "bad.txt"
    good.write_text("ok", encoding="utf-8")
    bad.write_text("nope", encoding="utf-8")

    bad.chmod(0)

    # In some environments (e.g., running as root), chmod may not make the file unreadable.
    if os.access(bad, os.R_OK):
        pytest.skip('Cannot reliably make file unreadable in this environment')

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=[], directories=["./"]),
        blacklist=BlacklistConfig(),
        data_sampling=DataSamplingConfig(enabled=False),
        overwrite_mode="force",
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    ok = d.distill(src, dst, dry_run=False, overwrite_mode="force")

    bad.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert ok is False
    assert d.stats.errors >= 1
    assert (dst / "good.txt").exists()