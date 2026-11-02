# T-BOX Architecture — Phase 1

## Runtime flow
`tbox` launcher → `main.py` → `core.router` → core services / module registry → module entry script.

## Components
- `core/paths.py`: central user config/data paths.
- `core/config_manager.py`: defaults, load, validate root object, recover invalid JSON.
- `core/logger.py`: file logging.
- `core/registry.py`: discovers module manifests and validates entry path containment.
- `core/router.py`: CLI commands and interactive menu.
- `core/diagnostics.py`: non-invasive environment checks.
- `modules/*/manifest.json`: module metadata and entry point.

## Data locations
- Config: `~/.config/tbox/`
- Data: `~/.local/share/tbox/`
- Logs: `~/.local/share/tbox/logs/`
- Cache: `~/.local/share/tbox/cache/`
- Backups: `~/.local/share/tbox/backups/`

## Phase 1 scope boundaries
The package manager is intentionally limited to guided selection of bundled starter modules. Remote package installation, signed manifests, dependency resolution, rollback, and plugin sandboxing are Phase 2+ work. Module execution is not sandboxed.
