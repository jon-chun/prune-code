from __future__ import annotations
import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logging(log_dir: Path, verbose: bool = False) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'log_{timestamp}.txt'

    logger = logging.getLogger('prune_code')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)-8s | %(message)s'))

    fileh = logging.FileHandler(log_file, encoding='utf-8')
    fileh.setLevel(logging.DEBUG)
    fileh.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    logger.addHandler(console)
    logger.addHandler(fileh)
    logger.info(f'Logging initialized. Log file: {log_file}')
    return logger
