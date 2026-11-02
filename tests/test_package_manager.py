"""Tests for package-manager validation, archives, and lifecycle operations."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from core import package_manager as pm
from core.package_manager import PackageError, _validate_manifest


def make_archive(module_id="sample-plugin", version="1.0.0", extra=None):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps({
            "id": module_id,
            "version": version,
            "entry": "main.py",
            "dependencies": []
        }))
        archive.writestr("main.py", "PLUGIN_VERSION = {!r}\n".format(version))
        for name, data in (extra or {}).items():
            archive.writestr(name, data)
    return buffer.getvalue()


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
            "id": "sample-plugin", "version": "1.0.0",
            "entry": "main.py", "dependencies": []
        })
        try:
            result = _validate_manifest(folder, "sample-plugin", "1.0.0")
            self.assertEqual(result["id"], "sample-plugin")
        finally:
            temp.cleanup()

    def test_rejects_manifest_identity_mismatch(self):
        temp, folder = self.make_plugin({
            "id": "other-plugin", "version": "1.0.0",
            "entry": "main.py", "dependencies": []
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()

    def test_rejects_entry_outside_plugin_directory(self):
        temp, folder = self.make_plugin({
            "id": "sample-plugin", "version": "1.0.0",
            "entry": "../outside.py", "dependencies": []
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()

    def test_rejects_declared_dependencies_in_preview(self):
        temp, folder = self.make_plugin({
            "id": "sample-plugin", "version": "1.0.0",
            "entry": "main.py", "dependencies": ["requests"]
        })
        try:
            with self.assertRaises(PackageError):
                _validate_manifest(folder, "sample-plugin", "1.0.0")
        finally:
            temp.cleanup()


class ArchiveExtractionTests(unittest.TestCase):
    def test_extracts_valid_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "staging"
            pm._extract_archive(make_archive(), target, "sample-plugin", "1.0.0")
            self.assertTrue((target / "main.py").is_file())
            self.assertTrue((target / "manifest.json").is_file())

    def test_rejects_path_traversal(self):
        payload = make_archive(extra={"../escaped.txt": "not allowed"})
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "staging"
            with self.assertRaises(PackageError):
                pm._extract_archive(payload, target, "sample-plugin", "1.0.0")
            self.assertFalse((Path(temp) / "escaped.txt").exists())
            self.assertFalse(target.exists())

    def test_rejects_symbolic_link(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("manifest.json", json.dumps({
                "id": "sample-plugin", "version": "1.0.0",
                "entry": "main.py", "dependencies": []
            }))
            info = zipfile.ZipInfo("main.py")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, "target")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(PackageError):
                pm._extract_archive(buffer.getvalue(), Path(temp) / "stage",
                                    "sample-plugin", "1.0.0")


class PackageLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plugin_dir = self.root / "plugins"
        self.plugin_dir.mkdir()
        self.registry = self.root / "plugins.json"
        self.addCleanup(self.temp.cleanup)
        self.patches = [
            patch.object(pm, "PLUGIN_DIR", self.plugin_dir),
            patch.object(pm, "PLUGINS_FILE", self.registry),
            patch.object(pm, "ensure_dirs"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def package(self, version, archive):
        return {
            "id": "sample-plugin",
            "version": version,
            "archive_url": "https://packages.example.test/sample.zip",
            "sha256": hashlib.sha256(archive).hexdigest(),
            "_repository": "test"
        }

    def test_install_update_and_remove(self):
        first = make_archive(version="1.0.0")
        second = make_archive(version="1.1.0")
        with patch.object(pm, "_find_package",
                          side_effect=[self.package("1.0.0", first),
                                       self.package("1.1.0", second)]), \
             patch.object(pm, "_request", side_effect=[first, second]):
            pm.install_module("sample-plugin")
            self.assertEqual(pm.installed_plugins()["sample-plugin"]["version"], "1.0.0")
            self.assertIn("1.0.0", (self.plugin_dir / "sample-plugin" / "main.py").read_text())

            pm.install_module("sample-plugin", update=True)
            self.assertEqual(pm.installed_plugins()["sample-plugin"]["version"], "1.1.0")
            self.assertIn("1.1.0", (self.plugin_dir / "sample-plugin" / "main.py").read_text())

        pm.remove_module("sample-plugin")
        self.assertNotIn("sample-plugin", pm.installed_plugins())
        self.assertFalse((self.plugin_dir / "sample-plugin").exists())

    def test_checksum_mismatch_does_not_install(self):
        archive = make_archive()
        package = self.package("1.0.0", archive)
        package["sha256"] = "0" * 64
        with patch.object(pm, "_find_package", return_value=package), \
             patch.object(pm, "_request", return_value=archive):
            with self.assertRaises(PackageError):
                pm.install_module("sample-plugin")
        self.assertFalse((self.plugin_dir / "sample-plugin").exists())
        self.assertEqual(pm.installed_plugins(), {})



    def test_install_rolls_back_when_registry_write_fails(self):
        new_archive = make_archive(version="1.1.0")
        target = self.plugin_dir / "sample-plugin"
        target.mkdir()
        (target / "main.py").write_text("OLD VERSION", encoding="utf-8")
        initial = {"sample-plugin": {"version": "1.0.0", "repository": "test",
                                     "enabled": True}}
        self.registry.write_text(json.dumps(initial), encoding="utf-8")
        package = self.package("1.1.0", new_archive)
        with patch.object(pm, "_find_package", return_value=package), \
             patch.object(pm, "_request", return_value=new_archive), \
             patch.object(pm, "_write_json", side_effect=OSError("simulated write failure")):
            with self.assertRaises(OSError):
                pm.install_module("sample-plugin", update=True)
        self.assertEqual((target / "main.py").read_text(encoding="utf-8"), "OLD VERSION")
        self.assertFalse((self.plugin_dir / "sample-plugin.backup").exists())

    def test_remove_rolls_back_when_registry_write_fails(self):
        target = self.plugin_dir / "sample-plugin"
        target.mkdir()
        (target / "main.py").write_text("KEEP ME", encoding="utf-8")
        initial = {"sample-plugin": {"version": "1.0.0", "repository": "test",
                                     "enabled": True}}
        self.registry.write_text(json.dumps(initial), encoding="utf-8")
        with patch.object(pm, "_write_json", side_effect=OSError("simulated write failure")):
            with self.assertRaises(OSError):
                pm.remove_module("sample-plugin")
        self.assertEqual((target / "main.py").read_text(encoding="utf-8"), "KEEP ME")
        self.assertEqual(pm.installed_plugins(), initial)


class RequestSecurityTests(unittest.TestCase):
    def test_rejects_https_redirect_to_http(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def geturl(self):
                return "http://packages.example.test/payload"
            def read(self, size):
                return b"payload"

        with patch("core.package_manager.urllib.request.urlopen",
                   return_value=FakeResponse()):
            with self.assertRaises(PackageError):
                pm._request("https://packages.example.test/start", 1024)

    def test_rejects_credentials_in_url(self):
        with patch("core.package_manager.urllib.request.urlopen") as open_url:
            with self.assertRaises(PackageError):
                pm._request("https://user:secret@packages.example.test/index.json", 1024)
            open_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
