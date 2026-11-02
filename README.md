# T-BOX — Termux Toolbox

A modular command-line toolkit for Termux. Phase 1 provides the core CLI, guided installer, module discovery, configuration, logging, diagnostics, and starter modules.

## Requirements
- Android with [Termux](https://termux.dev/) installed from a maintained source.
- Python 3.9+
- Git
- No root required.

## Install from GitHub

Repository: https://github.com/Xane01/t-box-termux

```bash
pkg update && pkg upgrade
pkg install git
git clone https://github.com/Xane01/t-box-termux.git
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

```bash
bash "$HOME/.local/opt/t-box-termux/update.sh"
```

Or from a cloned repository, run `bash update.sh`. Uninstall program files with `bash uninstall.sh`; user configuration and data are intentionally preserved.

## Add a module

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

## Security notes
- Review code before installing or running third-party modules.
- Do not put API keys, passwords, or tokens in Git.
- Network and security utilities should only be used on systems and networks you own or are authorized to assess.
- Phase 1 module discovery is not a sandbox. A module runs with the same permissions as the Termux user.
- Keep Termux and installed packages updated.

## Development

```bash
python main.py list
python main.py doctor
```

Phase 1 deliberately uses Python's standard library only. Optional terminal styling and third-party integrations can be introduced in later phases.
