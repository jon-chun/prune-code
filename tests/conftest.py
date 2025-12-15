import sys
from pathlib import Path

# Ensure local 'src' layout is importable when running pytest without installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
