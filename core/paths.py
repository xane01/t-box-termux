"""Centralized filesystem paths for T-BOX."""
import os
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = Path(os.environ.get("TBOX_CONFIG_DIR", HOME / ".config" / "tbox")).expanduser()
DATA_DIR = Path(os.environ.get("TBOX_DATA_DIR", HOME / ".local" / "share" / "tbox")).expanduser()
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
BACKUP_DIR = DATA_DIR / "backups"
CONFIG_FILE = CONFIG_DIR / "settings.json"
INSTALLED_FILE = DATA_DIR / "installed.json"

def ensure_dirs():
    for path in (CONFIG_DIR, DATA_DIR, LOG_DIR, CACHE_DIR, BACKUP_DIR):
        path.mkdir(parents=True, exist_ok=True)
