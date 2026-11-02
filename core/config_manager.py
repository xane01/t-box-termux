"""JSON-based configuration with safe defaults."""
import json
from pathlib import Path
from .paths import CONFIG_FILE, ensure_dirs

DEFAULTS = {
    "app_name": "T-BOX",
    "version": "0.1.0",
    "theme": "default",
    "check_updates": False,
    "log_level": "INFO",
    "repository": "https://github.com/Xane01/tbox-termux"
}

def load_config():
    ensure_dirs()
    if not CONFIG_FILE.exists():
        save_config(DEFAULTS)
        return DEFAULTS.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Configuration root must be an object")
        merged = DEFAULTS.copy()
        merged.update(data)
        return merged
    except (OSError, json.JSONDecodeError, ValueError):
        backup = CONFIG_FILE.with_suffix(".invalid")
        try:
            CONFIG_FILE.replace(backup)
        except OSError:
            pass
        save_config(DEFAULTS)
        return DEFAULTS.copy()

def save_config(data):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def set_value(key, value):
    cfg = load_config()
    if key not in DEFAULTS:
        raise KeyError("Unknown setting: " + key)
    if key == "check_updates":
        value = str(value).lower() in ("1", "true", "yes", "on")
    cfg[key] = value
    save_config(cfg)
    return cfg
