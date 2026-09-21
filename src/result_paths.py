"""Allow isolated web jobs while preserving historical batch output paths."""
import os
from pathlib import Path


def results_dir():
    return Path(os.environ.get('KGH_RESULTS_DIR', Path(__file__).resolve().parent.parent / 'Analysis results'))
