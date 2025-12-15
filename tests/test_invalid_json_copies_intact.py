from __future__ import annotations
from pathlib import Path
from prune_code.sampling import sample_json

def test_invalid_json_is_copied_intact(tmp_path: Path):
    src = tmp_path / "bad.json"
    dst = tmp_path / "out.json"
    bad = "{ this is not json"
    src.write_text(bad, encoding="utf-8")
    sample_json(src, dst, head_rows=5, tail_rows=5)
    assert dst.read_text(encoding="utf-8") == bad
