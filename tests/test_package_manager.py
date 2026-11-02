"""Unit tests for package-manager manifest validation."""
import json
import tempfile
import unittest
from pathlib import Path

from core.package_manager import PackageError, _validate_manifest


class ManifestValidationTests(unittest.TestCase):
    def make_plugin(self, manifest):
        temp = tempfile.TemporaryDirectory()
        folder = Path(temp.name)
        (folder / "main.py").write_text("print('safe test')\n", encoding="utf-8")
        (folder / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return temp, folder

    def test_accepts_matching_dependency_free_manifest(self):
        temp, folder = self.make_plugin({
            "id": "sample-plugin",
            "version": "1.0.0",
            "entry": "main.py",
            "dependencies": []
        })
        try:
            result = _validate_manifest(folder, "sample-plugin", "1.0.0")
            self.assertEqual(result["id"], "sample-plugin")
        finally:
            temp.cleanup()

    def test_rejects_manifest_identity_mismatch(self):
        temp, folder = self.make_plugin({
            "id": "other-plugin",
            "version": "1.0.0",
            "entry": "main.py",
            "dependencies": []
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()

    def test_rejects_entry_outside_plugin_directory(self):
        temp, folder = self.make_plugin({
            "id": "sample-plugin",
            "version": "1.0.0",
            "entry": "../outside.py",
            "dependencies": []
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()

    def test_rejects_declared_dependencies_in_preview(self):
        temp, folder = self.make_plugin({
            "id": "sample-plugin",
            "version": "1.0.0",
            "entry": "main.py",
            "dependencies": ["requests"]
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
