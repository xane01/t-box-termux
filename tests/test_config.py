import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import config_manager

class ConfigTests(unittest.TestCase):
    def test_defaults_are_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_file = Path(tmp) / "settings.json"
            with patch.object(config_manager, "CONFIG_FILE", cfg_file), patch.object(config_manager, "ensure_dirs"):
                cfg = config_manager.load_config()
                self.assertEqual(cfg["app_name"], "T-BOX")
                self.assertTrue(cfg_file.exists())

if __name__ == "__main__":
    unittest.main()
