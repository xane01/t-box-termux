"""Discover bundled modules and validated installed plugins."""
import json
from pathlib import Path
from .paths import INSTALLED_FILE, DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "modules"
PLUGIN_DIR = DATA_DIR / "plugins"
PLUGINS_FILE = DATA_DIR / "plugins.json"


def _discover_in(directory):
    found = {}
    if not directory.exists():
        return found
    for manifest in directory.glob("*/manifest.json"):
        try:
            item = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(item, dict):
                continue
            module_id = item.get("id")
            entry = item.get("entry")
            if not isinstance(module_id, str) or not module_id.replace("-", "").replace("_", "").isalnum():
                continue
            if not isinstance(entry, str) or not entry or "\\" in entry:
                continue
            script = (manifest.parent / entry).resolve()
            if manifest.parent.resolve() not in script.parents or not script.is_file():
                continue
            item["_script"] = script
            item["_directory"] = manifest.parent
            found[module_id] = item
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
    return found


def discover_modules():
    found = _discover_in(MODULES_DIR)
    # Install profiles restrict bundled modules to the selected starter set.
    if INSTALLED_FILE.exists():
        try:
            installed = json.loads(INSTALLED_FILE.read_text(encoding="utf-8"))
            if isinstance(installed, dict):
                found = {key: value for key, value in found.items()
                         if key in installed and isinstance(installed[key], dict)
                         and installed[key].get("enabled", True)}
        except (OSError, json.JSONDecodeError):
            return {}
    # Third-party plugins are discovered only when recorded as installed.
    try:
        plugins = json.loads(PLUGINS_FILE.read_text(encoding="utf-8"))
        if isinstance(plugins, dict):
            candidates = _discover_in(PLUGIN_DIR)
            for key, value in candidates.items():
                record = plugins.get(key)
                if isinstance(record, dict) and record.get("enabled", True):
                    found[key] = value
    except (OSError, json.JSONDecodeError):
        pass
    return found


def get_module(module_id):
    return discover_modules().get(module_id)
