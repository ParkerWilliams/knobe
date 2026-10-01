"""Puts the study folder on sys.path so tests can `import kmp`."""
import sys
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parents[1]
if str(STUDY_DIR) not in sys.path:
    sys.path.insert(0, str(STUDY_DIR))
