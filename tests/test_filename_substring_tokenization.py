import logging
from pathlib import Path

from prune_code.config import DistillerConfig
from prune_code.distiller import RepositoryDistiller, FilterAction

def _write_config(path: Path, data: str) -> Path:
    path.write_text(data, encoding="utf-8")
    return path

def test_substring_old_does_not_match_gold_in_whitelisted_file(tmp_path: Path):
    # Arrange: repo with the target file name containing 'gold' (should NOT match 'OLD')
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    target = repo / "src" / "step5_qa-gold-dataset.py"
    target.write_text("print('ok')\n", encoding="utf-8")

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, """ai_coding_env: 'chat'
max_file_size_mb: 5
overwrite_mode: "force"
whitelist:
  files:
    - "src/step5_qa-gold-dataset.py"
  directories: []
blacklist:
  files: []
  extensions: []
  patterns: []
  directories: []
  datetime_stamp_yyyymmdd: false
  filename_substrings: ["OLD"]
data_sampling:
  enabled: false
  target_extensions: []
  include_header: true
  head_rows: 5
  tail_rows: 5
""")

    logger = logging.getLogger("test")
    config = DistillerConfig.from_yaml(cfg_path, logger=logger)
    distiller = RepositoryDistiller(config, logger)

    # Act
    action, reason = distiller.determine_action(target, repo)

    # Assert
    assert action == FilterAction.COPY, f"Expected COPY but got {action} reason={reason}"

def test_substring_bu_does_not_match_inside_word(tmp_path: Path):
    # Arrange: file contains 'syallbus' which previously triggered 'BU' via naive substring match
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "kenyon_syllabus_iphs391_syallbus-revised-for-cpc.md"
    target.write_text("x", encoding="utf-8")

    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path, """ai_coding_env: 'chat'
max_file_size_mb: 5
overwrite_mode: "force"
whitelist:
  files:
    - "kenyon_syllabus_iphs391_syallbus-revised-for-cpc.md"
  directories: []
blacklist:
  files: []
  extensions: []
  patterns: []
  directories: []
  datetime_stamp_yyyymmdd: false
  filename_substrings: ["BU"]
data_sampling:
  enabled: false
  target_extensions: []
  include_header: true
  head_rows: 5
  tail_rows: 5
""")

    logger = logging.getLogger("test")
    config = DistillerConfig.from_yaml(cfg_path, logger=logger)
    distiller = RepositoryDistiller(config, logger)

    action, reason = distiller.determine_action(target, repo)

    assert action == FilterAction.COPY, f"Expected COPY but got {action} reason={reason}"
