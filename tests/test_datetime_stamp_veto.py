from __future__ import annotations
from pathlib import Path

import prune_code.distiller as dist
from prune_code.config import DistillerConfig, WhitelistConfig, BlacklistConfig, DataSamplingConfig
from prune_code.distiller import RepositoryDistiller, FilterAction

class DummyLogger:
    def info(self, *a, **k): pass
    def debug(self, *a, **k): pass
    def error(self, *a, **k): pass

def test_valid_yyyymmdd_stamp_is_vetoed(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "report_20251207.txt"
    f.write_text("x", encoding="utf-8")

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=[], directories=["./"]),
        blacklist=BlacklistConfig(datetime_stamp_yyyymmdd=True),
        data_sampling=DataSamplingConfig(enabled=False),
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    dist.FLAG_SAFER_BLACKLIST = True
    action, reason = d.determine_action(f, repo)
    assert action == FilterAction.SKIP
    assert reason == "tier2_blacklist_datetime_stamp:20251207"

def test_invalid_date_like_20251340_not_vetoed(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "report_20251340.txt"
    f.write_text("x", encoding="utf-8")

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=[], directories=["./"]),
        blacklist=BlacklistConfig(datetime_stamp_yyyymmdd=True),
        data_sampling=DataSamplingConfig(enabled=False),
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    dist.FLAG_SAFER_BLACKLIST = True
    action, _ = d.determine_action(f, repo)
    assert action == FilterAction.COPY
