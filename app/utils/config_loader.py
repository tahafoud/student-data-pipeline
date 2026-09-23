"""
config_loader.py
-----------------
Loads config.yaml once and exposes it as a plain dict. Keeping this in
one place means every module reads configuration the same way, and
new data sources / paths can be added by editing config.yaml only
(see the "Reusable Architecture" excellence requirement).
"""

from pathlib import Path
from typing import Any, Dict

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

_CACHED_CONFIG: Dict[str, Any] | None = None


def load_config() -> Dict[str, Any]:
    global _CACHED_CONFIG
    if _CACHED_CONFIG is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _CACHED_CONFIG = yaml.safe_load(f)
    return _CACHED_CONFIG


def resolve_path(relative_path: str) -> Path:
    """Resolve a path from config.yaml relative to the project root."""
    return PROJECT_ROOT / relative_path
