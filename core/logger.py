"""Small rotating-by-date log helper."""
import logging
from datetime import date
from .paths import LOG_DIR, ensure_dirs

def get_logger(name="tbox"):
    ensure_dirs()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / (date.today().isoformat() + ".log"), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
