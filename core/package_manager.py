"""Safe, manifest-driven package manager for T-BOX plugins.

Repositories publish an index.json with this shape:
{"modules":[{"id":"example-tool","version":"1.0.0","description":"...","archive_url":"https://.../example-tool.zip","sha256":"<64 hex chars>"}]}
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from .paths import DATA_DIR, ensure_dirs

REPOSITORIES_FILE = DATA_DIR / "repositories.json"
PLUGINS_FILE = DATA_DIR / "plugins.json"
PLUGIN_DIR = DATA_DIR / "plugins"
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_UNPACKED_BYTES = 50 * 1024 * 1024
MODULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
USER_AGENT = "TBOX-Termux-PackageManager/0.2.0"


class PackageError(Exception):
    """Expected package-manager error safe to show in the CLI."""


def _read_json(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, (dict, list)) else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path, value):
    ensure_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _request(url, limit):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise PackageError("Only valid HTTPS URLs are allowed.")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if parsed.username or parsed.password:
        raise PackageError("Credentials in repository URLs are not allowed.")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            final_url = urllib.parse.urlparse(response.geturl())
            if final_url.scheme != "https" or not final_url.netloc:
                raise PackageError("HTTPS downgrade or invalid redirect rejected.")
            data = response.read(limit + 1)
    except PackageError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PackageError("Download failed: {}".format(exc))
    if len(data) > limit:
        raise PackageError("Remote file exceeds the allowed size limit.")
    return data


def list_repositories():
    repos = _read_json(REPOSITORIES_FILE, {})
    return repos if isinstance(repos, dict) else {}


def add_repository(name, index_url):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,31}", name):
        raise PackageError("Repository name must be 2-32 letters, digits, '_' or '-'.")
    parsed = urllib.parse.urlparse(index_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise PackageError("Repository index must use HTTPS.")
    # Verify the index before saving the source.
    index = json.loads(_request(index_url, 1024 * 1024).decode("utf-8"))
    if not isinstance(index, dict) or not isinstance(index.get("modules"), list):
        raise PackageError("Invalid repository index: expected a modules array.")
    repos = list_repositories()
    repos[name] = index_url
    _write_json(REPOSITORIES_FILE, repos)
    return len(index["modules"])


def remove_repository(name):
    repos = list_repositories()
    if name not in repos:
        raise PackageError("Unknown repository: " + name)
    del repos[name]
    _write_json(REPOSITORIES_FILE, repos)


def _load_indexes():
    result = []
    for name, url in list_repositories().items():
        try:
            payload = json.loads(_request(url, 1024 * 1024).decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("modules"), list):
                continue
            for item in payload["modules"]:
                if isinstance(item, dict) and MODULE_ID_RE.fullmatch(str(item.get("id", ""))):
                    item = dict(item)
                    item["_repository"] = name
                    result.append(item)
        except (PackageError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    return result


def search_modules(query=""):
    query = query.lower().strip()
    return [item for item in _load_indexes()
            if not query or query in str(item.get("id", "")).lower()
            or query in str(item.get("name", "")).lower()
            or query in str(item.get("description", "")).lower()]


def _find_package(module_id):
    matches = [item for item in _load_indexes() if item.get("id") == module_id]
    if not matches:
        raise PackageError("Module not found in configured repositories: " + module_id)
    if len(matches) > 1:
        raise PackageError("Module ID exists in multiple repositories; use a unique ID.")
    return matches[0]


def installed_plugins():
    value = _read_json(PLUGINS_FILE, {})
    return value if isinstance(value, dict) else {}


def _validate_manifest(folder, expected_id, expected_version):
    manifest_path = folder / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise PackageError("Plugin archive must contain a valid manifest.json.")
    if not isinstance(manifest, dict):
        raise PackageError("Plugin manifest must be a JSON object.")
    module_id = manifest.get("id")
    version = manifest.get("version")
    entry = manifest.get("entry")
    if module_id != expected_id or version != expected_version:
        raise PackageError("Manifest ID/version does not match repository index.")
    if not isinstance(entry, str) or not entry or "\\" in entry:
        raise PackageError("Invalid manifest entry path.")
    entry_path = (folder / entry).resolve()
    if folder.resolve() not in entry_path.parents or not entry_path.is_file():
        raise PackageError("Plugin entry must be a file inside its module directory.")
    if manifest.get("dependencies", []) not in ([], None):
        raise PackageError("This release supports dependency-free plugins only.")
    return manifest


def _extract_archive(archive_bytes, target, expected_id, expected_version):
    temp = Path(tempfile.mkdtemp(prefix="tbox-plugin-"))
    try:
        archive_path = temp / "plugin.zip"
        archive_path.write_bytes(archive_bytes)
        total = 0
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                member = PurePosixPath(info.filename)
                if member.is_absolute() or ".." in member.parts:
                    raise PackageError("Unsafe path found in plugin archive.")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise PackageError("Symbolic links are not allowed in plugin archives.")
                total += info.file_size
                if total > MAX_UNPACKED_BYTES:
                    raise PackageError("Unpacked plugin exceeds the size limit.")
            archive.extractall(temp / "unpacked")
        root = temp / "unpacked"
        candidates = [root]
        candidates.extend(path for path in root.iterdir() if path.is_dir())
        source = None
        for candidate in candidates:
            if (candidate / "manifest.json").is_file():
                source = candidate
                break
        if source is None:
            raise PackageError("Archive does not contain manifest.json at its root.")
        _validate_manifest(source, expected_id, expected_version)
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def install_module(module_id, update=False):
    if not MODULE_ID_RE.fullmatch(module_id):
        raise PackageError("Invalid module ID.")
    bundled_dir = Path(__file__).resolve().parents[1] / "modules"
    for manifest_path in bundled_dir.glob("*/manifest.json"):
        try:
            bundled = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(bundled, dict) and bundled.get("id") == module_id:
                raise PackageError("Plugin ID conflicts with a bundled T-BOX module.")
        except (OSError, json.JSONDecodeError):
            continue
    package = _find_package(module_id)
    version = str(package.get("version", ""))
    if not version:
        raise PackageError("Repository package is missing a version.")
    archive_url = package.get("archive_url")
    if not isinstance(archive_url, str):
        raise PackageError("Repository package is missing archive_url.")
    expected_hash = package.get("sha256")
    if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
        raise PackageError("Package index must provide a valid SHA-256 checksum.")
    current = installed_plugins()
    if module_id in current and not update:
        raise PackageError("Module is already installed. Use 'tbox update " + module_id + "'.")
    archive = _request(archive_url, MAX_ARCHIVE_BYTES)
    actual_hash = hashlib.sha256(archive).hexdigest()
    if actual_hash.lower() != expected_hash.lower():
        raise PackageError("SHA-256 checksum mismatch; plugin was not installed.")
    ensure_dirs()
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    target = PLUGIN_DIR / module_id
    staging = PLUGIN_DIR / (module_id + ".staging")
    backup = PLUGIN_DIR / (module_id + ".backup")
    if staging.exists():
        shutil.rmtree(staging)
    _extract_archive(archive, staging, module_id, version)
    if backup.exists():
        shutil.rmtree(backup)
    had_target = target.exists()
    if had_target:
        target.rename(backup)
    try:
        staging.rename(target)
        current[module_id] = {
            "version": version,
            "repository": package["_repository"],
            "enabled": True
        }
        _write_json(PLUGINS_FILE, current)
    except Exception:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        if backup.exists():
            backup.rename(target)
        raise
    if backup.exists():
        shutil.rmtree(backup)
    return package


def remove_module(module_id):
    current = installed_plugins()
    if module_id not in current:
        raise PackageError("Plugin is not installed: " + module_id)
    target = PLUGIN_DIR / module_id
    backup = PLUGIN_DIR / (module_id + ".removing")
    if backup.exists():
        shutil.rmtree(backup)
    had_target = target.exists()
    if had_target:
        target.rename(backup)
    del current[module_id]
    try:
        _write_json(PLUGINS_FILE, current)
    except Exception:
        if backup.exists() and not target.exists():
            backup.rename(target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def update_modules(module_id=None):
    current = installed_plugins()
    targets = [module_id] if module_id else sorted(current)
    updated, failed = [], []
    for item in targets:
        if item not in current:
            failed.append((item, "not installed"))
            continue
        try:
            package = install_module(item, update=True)
            updated.append((item, package.get("version", "unknown")))
        except PackageError as exc:
            failed.append((item, str(exc)))
    return updated, failed
