"""Non-invasive installation diagnostics."""
import os
import platform
import shutil
import sys
from .paths import CONFIG_DIR, DATA_DIR, ensure_dirs

def run_doctor():
    ensure_dirs()
    is_termux = "com.termux" in os.environ.get("PREFIX", "") or "termux" in platform.platform().lower()
    results = [
        ("Python 3", sys.version_info >= (3, 9), sys.version.split()[0]),
        ("Termux environment", is_termux, os.environ.get("PREFIX", "not detected")),
        ("Git", shutil.which("git") is not None, shutil.which("git") or "not found"),
        ("Config directory", CONFIG_DIR.exists(), str(CONFIG_DIR)),
        ("Data directory", DATA_DIR.exists(), str(DATA_DIR)),
        ("Write access", os.access(DATA_DIR, os.W_OK), "T-BOX data directory"),
    ]
    return results
