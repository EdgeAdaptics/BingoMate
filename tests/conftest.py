"""Pytest configuration and fixtures."""
from __future__ import annotations

import pytest
from pathlib import Path
import sys

# Add the project root to sys.path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
