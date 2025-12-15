from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

import yaml

@dataclass(frozen=True)
class BlacklistConfig:
    files: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    patterns: List[re.Pattern] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    datetime_stamp_yyyymmdd: bool = True
    filename_substrings: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class WhitelistConfig:
    files: List[str] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class DataSamplingConfig:
    enabled: bool = True
    target_extensions: Set[str] = field(default_factory=set)
    include_header: bool = True
    head_rows: int = 5
    tail_rows: int = 5

@dataclass(frozen=True)
class DistillerConfig:
    ai_coding_env: str = 'chat'
    max_file_size_mb: float = 5.0
    overwrite_mode: str = 'prompt'  # prompt|force|fail
    whitelist: WhitelistConfig = field(default_factory=WhitelistConfig)
    blacklist: BlacklistConfig = field(default_factory=BlacklistConfig)
    data_sampling: DataSamplingConfig = field(default_factory=DataSamplingConfig)

    @staticmethod
    def from_yaml(config_path: Path, logger: Optional[logging.Logger] = None) -> 'DistillerConfig':
        logger = logger or logging.getLogger(__name__)
        config_path = config_path.resolve()

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # Compile regex patterns
        compiled = []
        for pattern_str in (data.get('blacklist', {}) or {}).get('patterns', []) or []:
            try:
                compiled.append(re.compile(pattern_str))
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern_str}': {e}")

        # Normalize extensions
        exts = (data.get('blacklist', {}) or {}).get('extensions', []) or []
        normalized_exts = [e if e.startswith('.') else f'.{e}' for e in exts]

        # Data sampling extensions
        ds = data.get('data_sampling', {}) or {}
        ds_exts = ds.get('target_extensions', []) or []
        normalized_ds_exts = {e if e.startswith('.') else f'.{e}' for e in ds_exts}

        whitelist = data.get('whitelist', {}) or {}
        blacklist = data.get('blacklist', {}) or {}

        return DistillerConfig(
            ai_coding_env=data.get('ai_coding_env', 'chat'),
            max_file_size_mb=float(data.get('max_file_size_mb', 5.0)),
            overwrite_mode=str(data.get('overwrite_mode', 'prompt')).lower(),
            whitelist=WhitelistConfig(
                files=whitelist.get('files', []) or [],
                directories=whitelist.get('directories', []) or [],
            ),
            blacklist=BlacklistConfig(
                files=blacklist.get('files', []) or [],
                extensions=normalized_exts,
                patterns=compiled,
                directories=blacklist.get('directories', []) or [],
                datetime_stamp_yyyymmdd=bool(blacklist.get('datetime_stamp_yyyymmdd', True)),
                filename_substrings=blacklist.get('filename_substrings', []) or [],
            ),
            data_sampling=DataSamplingConfig(
                enabled=bool(ds.get('enabled', True)),
                target_extensions=normalized_ds_exts,
                include_header=bool(ds.get('include_header', True)),
                head_rows=int(ds.get('head_rows', 5)),
                tail_rows=int(ds.get('tail_rows', 5)),
            ),
        )
