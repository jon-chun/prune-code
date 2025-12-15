from __future__ import annotations
from pathlib import Path

from prune_code.config import DistillerConfig, WhitelistConfig, BlacklistConfig, DataSamplingConfig
from prune_code.distiller import RepositoryDistiller

class DummyLogger:
    def info(self, *a, **k): pass
    def debug(self, *a, **k): pass
    def error(self, *a, **k): pass

def test_overwrite_fail_returns_false(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    (src / "a.txt").write_text("x", encoding="utf-8")

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=[], directories=["./"]),
        blacklist=BlacklistConfig(),
        data_sampling=DataSamplingConfig(enabled=False),
        overwrite_mode="fail",
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    ok = d.distill(src, dst, dry_run=False, overwrite_mode="fail")
    assert ok is False
