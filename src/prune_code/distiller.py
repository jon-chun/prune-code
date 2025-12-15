from __future__ import annotations
import re
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import DistillerConfig
from .sampling import atomic_copy, sample_csv_tsv, sample_json, sample_jsonl

# Global var requested by user.
FLAG_SAFER_BLACKLIST: bool = True

class FilterAction(Enum):
    COPY = 'COPY'
    SAMPLE = 'SAMPLE'
    SKIP = 'SKIP'

@dataclass
class FilterStats:
    scanned: int = 0
    copied: int = 0
    sampled: int = 0
    skipped: int = 0
    errors: int = 0
    skipped_reasons: Dict[str, int] = field(default_factory=dict)

    def add_skip_reason(self, reason: str) -> None:
        self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + 1

_YYYYMMDD_RE = re.compile(r"(19\d{2}|20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])")

def _is_valid_yyyymmdd(token: str) -> bool:
    try:
        import datetime
        datetime.date(int(token[0:4]), int(token[4:6]), int(token[6:8]))
        return True
    except Exception:
        return False

class RepositoryDistiller:
    def __init__(self, config: DistillerConfig, logger):
        self.config = config
        self.logger = logger
        self.stats = FilterStats()

    def _rel(self, path: Path, base: Path) -> Optional[Path]:
        try:
            return path.resolve().relative_to(base.resolve())
        except ValueError:
            return None

    def _match_any(self, rel: Path, patterns) -> bool:
        rel_str = str(rel).replace('\\', '/')
        for pat in patterns:
            p = str(pat).strip().lstrip('./')
            if p in ('', '.'):  # repo root / match-all
                return True
            if p.endswith('/'):
                if rel_str.startswith(p.rstrip('/')):
                    return True
            if rel_str == p.rstrip('/'):
                return True
            if '*' in p or '?' in p or '[' in p:
                try:
                    if rel.match(p.rstrip('/')):
                        return True
                except Exception:
                    pass
        return False

    def _explicit_whitelist_file(self, rel: Path) -> bool:
        return self._match_any(rel, self.config.whitelist.files)

    def _explicit_blacklist_file(self, rel: Path) -> bool:
        return self._match_any(rel, self.config.blacklist.files)

    def _is_in_any_whitelist_dir(self, rel: Path) -> bool:
        return self._match_any(rel, self.config.whitelist.directories)

    def _in_blacklisted_dir(self, rel: Path) -> bool:
        return self._match_any(rel, self.config.blacklist.directories)

    def _should_sample(self, path: Path) -> bool:
        return self.config.data_sampling.enabled and path.suffix.lower() in self.config.data_sampling.target_extensions

    def _tier2_veto(self, rel: Path, filename: str) -> Optional[Tuple[FilterAction, str]]:
        # Explicit blacklist file rules
        if self._explicit_blacklist_file(rel):
            return FilterAction.SKIP, 'tier2_blacklist_file'

        # Regex blacklist rules (applied to the filename)
        for pat in self.config.blacklist.patterns:
            if pat.search(filename):
                return FilterAction.SKIP, f'tier2_blacklist_pattern:{pat.pattern}'

        # Datestamp veto
        if self.config.blacklist.datetime_stamp_yyyymmdd:
            m = _YYYYMMDD_RE.search(filename)
            if m:
                token = m.group(0)
                if _is_valid_yyyymmdd(token):
                    return FilterAction.SKIP, f'tier2_blacklist_datetime_stamp:{token}'

        # Token-based filename substring vetoes (avoid false positives like OLD in GOLD)
        stem_upper = Path(filename).stem.upper()
        tokens = [t for t in re.split(r'[^A-Z0-9]+', stem_upper) if t]
        token_set = set(tokens)

        for tok in (self.config.blacklist.filename_substrings or []):
            tok_u = str(tok).upper()
            if tok_u in token_set:
                return FilterAction.SKIP, f'tier2_blacklist_filename_substring:{tok}'

        return None

    def _tier1_include(self, rel: Path, path: Path) -> Optional[Tuple[FilterAction, str]]:
        if self._explicit_whitelist_file(rel):
            if self._should_sample(path):
                return (FilterAction.SAMPLE, 'tier1_whitelist_file_sampled')
            return (FilterAction.COPY, 'tier1_whitelist_file')
        return None

    def determine_action(self, path: Path, base: Path) -> Tuple[FilterAction, Optional[str]]:
        path = path.resolve()
        base = base.resolve()
        rel = self._rel(path, base)
        if rel is None:
            return FilterAction.SKIP, 'outside_root'
        filename = path.name

        if FLAG_SAFER_BLACKLIST:
            v = self._tier2_veto(rel, filename)
            if v:
                return v
            i = self._tier1_include(rel, path)
            if i:
                return i
        else:
            i = self._tier1_include(rel, path)
            if i:
                return i
            v = self._tier2_veto(rel, filename)
            if v:
                return v

        if not self._is_in_any_whitelist_dir(rel):
            return FilterAction.SKIP, 'tier3_not_in_whitelist_scope'

        if self._in_blacklisted_dir(rel):
            return FilterAction.SKIP, 'tier4_blacklist_directory'

        ext = path.suffix.lower()
        if ext in self.config.blacklist.extensions:
            return FilterAction.SKIP, f'tier4_blacklist_extension:{ext}'

        try:
            size_mb = path.stat().st_size / (1024 * 1024)
        except OSError:
            return FilterAction.SKIP, 'tier4_stat_failed'
        if size_mb > self.config.max_file_size_mb:
            return FilterAction.SKIP, f'tier4_file_size_limit_exceeded:{self.config.max_file_size_mb}MB'

        if self._should_sample(path):
            return FilterAction.SAMPLE, 'sampled_in_scope'
        return FilterAction.COPY, 'copied_in_scope'

    def _write(self, src: Path, dst: Path, action: FilterAction) -> None:
        if action == FilterAction.COPY:
            atomic_copy(src, dst)
            self.stats.copied += 1
            return
        if action == FilterAction.SAMPLE:
            ext = src.suffix.lower()
            if ext in ('.csv', '.tsv'):
                sample_csv_tsv(
                    src, dst,
                    include_header=self.config.data_sampling.include_header,
                    head_rows=self.config.data_sampling.head_rows,
                    tail_rows=self.config.data_sampling.tail_rows,
                    delimiter='\t' if ext == '.tsv' else None,
                )
            elif ext == '.jsonl':
                sample_jsonl(src, dst, head_rows=self.config.data_sampling.head_rows, tail_rows=self.config.data_sampling.tail_rows)
            elif ext == '.json':
                sample_json(src, dst, head_rows=self.config.data_sampling.head_rows, tail_rows=self.config.data_sampling.tail_rows)
            else:
                atomic_copy(src, dst)
            self.stats.sampled += 1
            return
        # SKIP handled upstream

    def distill(self, source_dir: Path, dest_dir: Path, *, dry_run: bool = False, overwrite_mode: Optional[str] = None) -> bool:
        source_dir = source_dir.resolve()
        dest_dir = dest_dir.resolve()
        overwrite_mode = (overwrite_mode or self.config.overwrite_mode or 'prompt').lower()

        self.logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting prune...")
        self.logger.info(f"Source: {source_dir}")
        self.logger.info(f"Destination: {dest_dir}")
        self.logger.info(f"Safer blacklist precedence: {FLAG_SAFER_BLACKLIST}")

        if not source_dir.exists() or not source_dir.is_dir():
            self.logger.error(f"Source directory invalid: {source_dir}")
            return False

        if not dry_run:
            if dest_dir.exists():
                if overwrite_mode == 'fail':
                    self.logger.error(f"Destination exists and overwrite_mode=fail: {dest_dir}")
                    return False
                if overwrite_mode == 'prompt' and not self._confirm_overwrite(dest_dir):
                    self.logger.info('Operation cancelled by user.')
                    return False
                shutil.rmtree(dest_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

        for p in source_dir.rglob('*'):
            if not p.is_file():
                continue
            self.stats.scanned += 1
            action, reason = self.determine_action(p, source_dir)
            rel = self._rel(p, source_dir)
            rel_str = str(rel) if rel else str(p)

            if action == FilterAction.SKIP:
                self.stats.skipped += 1
                if reason:
                    self.stats.add_skip_reason(reason)
                self.logger.debug(f"SKIP[{reason}]: {rel_str}")
                continue

            if dry_run:
                self.logger.info(f"[DRY RUN] {action.value}: {rel_str}")
                if action == FilterAction.COPY:
                    self.stats.copied += 1
                elif action == FilterAction.SAMPLE:
                    self.stats.sampled += 1
                continue

            dst = dest_dir / rel
            try:
                self._write(p, dst, action)
            except Exception as e:
                self.stats.errors += 1
                self.logger.error(f"Error processing {rel_str}: {e}")

        self._print_summary()
        return self.stats.errors == 0

    def _confirm_overwrite(self, dest_dir: Path) -> bool:
        print(f"\nWARNING: Destination directory exists: {dest_dir}")
        print("All contents will be deleted. Continue? (yes/no): ", end='')
        try:
            resp = input().strip().lower()
            return resp in {'yes', 'y'}
        except (EOFError, KeyboardInterrupt):
            print()
            return False

    def _print_summary(self) -> None:
        self.logger.info("\n" + "=" * 70)
        self.logger.info("PRUNE SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total files scanned:  {self.stats.scanned}")
        self.logger.info(f"Files copied:         {self.stats.copied}")
        self.logger.info(f"Files sampled:        {self.stats.sampled}")
        self.logger.info(f"Files skipped:        {self.stats.skipped}")
        self.logger.info(f"Errors:               {self.stats.errors}")
        if self.stats.skipped_reasons:
            self.logger.info("\nSkip reasons breakdown:")
            for reason, count in sorted(self.stats.skipped_reasons.items(), key=lambda x: -x[1]):
                self.logger.info(f"  {reason:40s}: {count:>6d}")
        self.logger.info("=" * 70 + "\n")