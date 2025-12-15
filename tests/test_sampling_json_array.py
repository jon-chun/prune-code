from __future__ import annotations
import json
from pathlib import Path

from prune_code.sampling import sample_json

def test_json_array_sampling_structure(tmp_path: Path):
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"

    src.write_text(json.dumps(list(range(30))), encoding="utf-8")
    sample_json(src, dst, head_rows=5, tail_rows=5)

    out = json.loads(dst.read_text(encoding="utf-8"))
    assert out["_sampled"] is True
    assert out["_total_items"] == 30
    assert out["_omitted_items"] == 20
    assert out["head"] == [0, 1, 2, 3, 4]
    assert out["tail"] == [25, 26, 27, 28, 29]
