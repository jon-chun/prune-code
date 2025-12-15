from __future__ import annotations
import csv
import json
import shutil
from collections import deque
from pathlib import Path
from typing import Optional

def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + '.tmp')
    shutil.copy2(source, tmp)
    tmp.replace(destination)

def sample_csv_tsv(
    source: Path,
    destination: Path,
    *,
    include_header: bool,
    head_rows: int,
    tail_rows: int,
    delimiter: Optional[str] = None
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + '.tmp')

    tail = deque(maxlen=max(0, tail_rows))
    head = []
    total_data = 0

    with open(source, 'r', encoding='utf-8', newline='', errors='replace') as src:
        reader = csv.reader(src, delimiter=delimiter) if delimiter else csv.reader(src)

        first = next(reader, None)
        if first is None:
            atomic_copy(source, destination)
            return

        header_row = first if include_header else None
        if not include_header:
            total_data += 1
            if len(head) < head_rows:
                head.append(first)
            tail.append(first)

        for row in reader:
            total_data += 1
            if len(head) < head_rows:
                head.append(row)
            tail.append(row)

    if total_data <= head_rows + tail_rows:
        atomic_copy(source, destination)
        return

    omitted = total_data - len(head) - len(tail)
    with open(tmp, 'w', encoding='utf-8', newline='') as dst:
        writer = csv.writer(dst, delimiter=delimiter) if delimiter else csv.writer(dst)
        if header_row is not None:
            writer.writerow(header_row)
        writer.writerows(head)
        writer.writerow([f"... ({omitted} rows omitted) ..."])
        writer.writerows(list(tail))

    tmp.replace(destination)

def sample_jsonl(source: Path, destination: Path, *, head_rows: int, tail_rows: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + '.tmp')

    head = []
    tail = deque(maxlen=max(0, tail_rows))
    total = 0

    with open(source, 'r', encoding='utf-8', errors='replace') as src:
        for raw in src:
            line = raw.rstrip('\n\r')
            if not line.strip():
                continue
            total += 1
            if len(head) < head_rows:
                head.append(line)
            tail.append(line)

    if total == 0 or total <= head_rows + tail_rows:
        atomic_copy(source, destination)
        return

    omitted = total - len(head) - len(tail)
    with open(tmp, 'w', encoding='utf-8') as dst:
        if head:
            dst.write('\n'.join(head))
            dst.write('\n\n')
        dst.write(f"... ({omitted} objects omitted) ...\n\n")
        dst.write('\n'.join(list(tail)))

    tmp.replace(destination)

def sample_json(source: Path, destination: Path, *, head_rows: int, tail_rows: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + '.tmp')

    content = source.read_text(encoding='utf-8', errors='replace').strip()
    try:
        data = json.loads(content) if content else None
    except json.JSONDecodeError:
        atomic_copy(source, destination)
        return

    if isinstance(data, list):
        total = len(data)
        h = max(0, int(head_rows))
        t = max(0, int(tail_rows))
        if total <= h + t:
            atomic_copy(source, destination)
            return
        head = data[:h]
        tail = data[-t:] if t > 0 else []
        sampled = {
            "_sampled": True,
            "_total_items": total,
            "_omitted_items": total - len(head) - len(tail),
            "head": head,
            "tail": tail,
        }
        tmp.write_text(json.dumps(sampled, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp.replace(destination)
        return

    atomic_copy(source, destination)
