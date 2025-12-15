from __future__ import annotations
from pathlib import Path

import prune_code.distiller as dist
from prune_code.config import DistillerConfig, WhitelistConfig, BlacklistConfig, DataSamplingConfig
from prune_code.distiller import RepositoryDistiller, FilterAction

class DummyLogger:
    def info(self, *a, **k): pass
    def debug(self, *a, **k): pass
    def error(self, *a, **k): pass

def test_flag_safer_blacklist_true_veto_wins(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "foo_BACKUP.txt"
    f.write_text("x", encoding="utf-8")

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=["foo_BACKUP.txt"], directories=["./"]),
        blacklist=BlacklistConfig(filename_substrings=["BACKUP"]),
        data_sampling=DataSamplingConfig(enabled=False),
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    dist.FLAG_SAFER_BLACKLIST = True
    action, reason = d.determine_action(f, repo)
    assert action == FilterAction.SKIP
    assert reason.startswith("tier2_blacklist_filename_substring")

def test_flag_safer_blacklist_false_whitelist_wins(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    f = repo / "foo_BACKUP.txt"
    f.write_text("x", encoding="utf-8")

    cfg = DistillerConfig(
        whitelist=WhitelistConfig(files=["foo_BACKUP.txt"], directories=["./"]),
        blacklist=BlacklistConfig(filename_substrings=["BACKUP"]),
        data_sampling=DataSamplingConfig(enabled=False),
    )
    d = RepositoryDistiller(cfg, DummyLogger())
    dist.FLAG_SAFER_BLACKLIST = False
    action, reason = d.determine_action(f, repo)
    assert action == FilterAction.COPY
    assert reason == "tier1_whitelist_file"
