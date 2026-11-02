import unittest
from core.registry import discover_modules

class RegistryTests(unittest.TestCase):
    def test_bundled_manifests_discovered(self):
        modules = discover_modules()
        self.assertIn("device-info", modules)
        self.assertIn("net-doctor", modules)
        self.assertIn("json-studio", modules)
        self.assertIn("hash-lab", modules)

if __name__ == "__main__":
    unittest.main()
