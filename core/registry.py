"""Discover module manifests from modules/*/manifest.json."""
import json
from pathlib import Path
from .paths import INSTALLED_FILE

ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "modules"

def discover_modules():
    found = {}
    if not MODULES_DIR.exists():
        return found
    for manifest in MODULES_DIR.glob("*/manifest.json"):
        try:
            item = json.loads(manifest.read_text(encoding="utf-8"))
            module_id = item.get("id")
            entry = item.get("entry")
            if not module_id or not entry or not module_id.replace("-", "").replace("_", "").isalnum():
                continue
            script = (manifest.parent / entry).resolve()
            if manifest.parent.resolve() not in script.parents or not script.is_file():
                continue
            item["_script"] = script
            item["_directory"] = manifest.parent
            found[module_id] = item
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
    # When an install profile exists, expose only explicitly enabled modules.
    # In a source checkout (no installed.json), expose every bundled module.
    if INSTALLED_FILE.exists():
        try:
            installed = json.loads(INSTALLED_FILE.read_text(encoding="utf-8"))
            if isinstance(installed, dict):
                found = {key: value for key, value in found.items()
                         if key in installed and installed[key].get("enabled", True)}
        except (OSError, json.JSONDecodeError, AttributeError):
            return {}
    return found

def get_module(module_id):
    return discover_modules().get(module_id)
