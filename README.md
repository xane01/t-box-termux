# TBOX TERMUX

A modular command-line toolkit for Termux. Version 0.2.0 introduces a manifest-driven plugin package manager alongside the core CLI, guided installer, module discovery, configuration, diagnostics, and starter modules.

## Requirements
- Android with [Termux](https://termux.dev/) installed from a maintained source.
- Python 3.9+
- Git
- No root required.

## Install from GitHub

Repository: https://github.com/xane01/t-box-termux

```bash
pkg update && pkg upgrade
pkg install git
git clone https://github.com/xane01/t-box-termux.git
cd t-box-termux
bash install.sh
```

The guided installer offers:
1. Minimal core
2. Core + starter tools
3. Individual starter tool selection

Then run:

```bash
tbox
tbox list
tbox info
tbox doctor
```

## Starter modules

```bash
tbox run device-info
tbox run net-doctor example.com --https
tbox run json-studio sample.json
tbox run hash-lab sample.zip --algorithm sha256
```

## Configuration

```bash
tbox config show
tbox config set theme default
tbox config set check_updates true
```

Settings live in `~/.config/tbox/settings.json`. Runtime data and logs live in `~/.local/share/tbox/`.

## Update and uninstall

Update the TBOX application source:

```bash
bash "$HOME/.local/opt/t-box-termux/update.sh"
```

Or, from a cloned source repository, run `bash update.sh`. This updates the TBOX application itself; it is separate from `tbox update`, which updates installed plugins.

Uninstall program files with `bash uninstall.sh`; user configuration and data are intentionally preserved.

## Add a bundled module

Create `modules/<folder>/manifest.json` and a Python entry script in the same folder.

Example manifest:

```json
{
  "id": "example-tool",
  "name": "Example Tool",
  "version": "0.1.0",
  "category": "general",
  "description": "Short description",
  "entry": "main.py",
  "dependencies": []
}
```

Run it with:

```bash
tbox run example-tool
```

Module IDs should be lowercase letters, digits, hyphens, or underscores. The entry script must remain inside its module directory.

## Package manager and plugin repositories

TBOX can search, install, inspect, update, and remove plugins from HTTPS repositories that publish an `index.json`. Plugin archives must include a root-level `manifest.json`, a valid entry script, and a SHA-256 checksum in the repository index.

```bash
tbox repo add community https://example.org/tbox/index.json
tbox repo list
tbox search
tbox search network
tbox install example-tool
tbox plugin-info example-tool
tbox list
tbox run example-tool
tbox update example-tool
tbox update
tbox remove example-tool
tbox repo remove community
```

`plugin-info` displays metadata for a plugin that is currently installed. If the plugin is not installed, TBOX reports that state explicitly.

Repository index format:

```json
{
  "modules": [
    {
      "id": "example-tool",
      "name": "Example Tool",
      "version": "1.0.0",
      "description": "Example plugin",
      "archive_url": "https://example.org/tbox/example-tool-1.0.0.zip",
      "sha256": "REPLACE_WITH_64_HEX_SHA256"
    }
  ]
}
```

The package manager currently accepts HTTPS only, limits downloads and extracted size, validates module IDs and manifest entry paths, rejects archive path traversal and symbolic links, and verifies SHA-256 before installation. Dependency resolution is intentionally deferred; plugins declaring dependencies are rejected in this release. Repositories are metadata sources, not trust authorities: a checksum detects archive mismatch but does not prove that plugin code is safe. Review third-party code before installation or execution. Plugins run with the same Termux user permissions as TBOX and are not sandboxed.

Repository and plugin state is stored under `~/.local/share/tbox/`; uninstalling program files does not remove that user data.

## Security notes
- Review code before installing or running third-party modules.
- Do not put API keys, passwords, or tokens in Git.
- Network and security utilities should only be used on systems and networks you own or are authorized to assess.
- Plugin execution is not sandboxed; plugins run with the same permissions as the Termux user.
- Keep Termux and installed packages updated.

## Development

```bash
python -m unittest discover -s tests -v
python main.py list
python main.py doctor
```

TBOX core and bundled modules use Python's standard library only. Optional terminal styling and third-party integrations can be introduced in later phases.
