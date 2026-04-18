"""Worker package bootstrap utilities."""

import sys
from pathlib import Path

# Make project-root modules importable when running from backend/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))
