#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_URL="${TBOX_REPO_URL:-https://github.com/xane01/t-box-termux.git}"
INSTALL_DIR="${TBOX_HOME:-$HOME/.local/opt/t-box-termux}"
BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

green='\033[1;32m'
yellow='\033[1;33m'
reset='\033[0m'

say() { printf "${green}[T-BOX]${reset} %s\n" "$*"; }
warn() { printf "${yellow}[T-BOX]${reset} %s\n" "$*"; }

if [ -z "${PREFIX:-}" ] || [ ! -d "$PREFIX" ]; then
  echo "This installer is intended for Termux."
  exit 1
fi

command -v pkg >/dev/null 2>&1 || {
  echo "Termux pkg command not found."
  exit 1
}

say "Installing prerequisites..."
pkg update -y
pkg install -y python git

mkdir -p "$(dirname "$INSTALL_DIR")" "$BIN_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
  say "Existing Git installation detected."
  git -C "$INSTALL_DIR" pull --ff-only
else
  say "Preparing repository clone..."

  TMP_ROOT="$(mktemp -d "$(dirname "$INSTALL_DIR")/.tbox-install.XXXXXX")"
  trap 'rm -rf "$TMP_ROOT"' EXIT

  git clone "$REPO_URL" "$TMP_ROOT/repo"

  if [ ! -f "$TMP_ROOT/repo/main.py" ] || [ ! -d "$TMP_ROOT/repo/core" ]; then
    echo "Invalid T-BOX repository."
    exit 1
  fi

  if [ -e "$INSTALL_DIR" ]; then
    warn "Replacing legacy installation without Git metadata."
    mv "$INSTALL_DIR" "$TMP_ROOT/legacy"
  fi

  if ! mv "$TMP_ROOT/repo" "$INSTALL_DIR"; then
    if [ -d "$TMP_ROOT/legacy" ]; then
      mv "$TMP_ROOT/legacy" "$INSTALL_DIR"
    fi
    echo "Installation failed. Previous installation restored."
    exit 1
  fi
fi

if [ ! -f "$INSTALL_DIR/main.py" ] || [ ! -d "$INSTALL_DIR/core" ]; then
  echo "T-BOX source validation failed."
  exit 1
fi

say "Choose installation profile:"
echo "  1) Minimal core"
echo "  2) Core + starter tools (recommended)"
echo "  3) Review individual starter tools"

read -r -p "Selection [1-3, default 2]: " profile
profile="${profile:-2}"

selected="device-info net-doctor json-studio hash-lab"

case "$profile" in
  1)
    selected=""
    ;;
  2)
    selected="device-info net-doctor json-studio hash-lab"
    ;;
  3)
    selected=""
    for item in device-info net-doctor json-studio hash-lab; do
      read -r -p "Install $item? [Y/n]: " answer
      case "${answer,,}" in
        n|no) ;;
        *) selected="$selected $item" ;;
      esac
    done
    ;;
  *)
    warn "Unknown selection; using starter tools."
    selected="device-info net-doctor json-studio hash-lab"
    ;;
esac

export TBOX_HOME="$INSTALL_DIR"

python - "$INSTALL_DIR" "$selected" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
selected = set(sys.argv[2].split())
installed = {}

for manifest in (root / "modules").glob("*/manifest.json"):
    item = json.loads(manifest.read_text(encoding="utf-8"))
    if item["id"] in selected:
        installed[item["id"]] = {
            "version": item.get("version", "0.0.0"),
            "enabled": True
        }

data = Path.home() / ".local" / "share" / "tbox"
data.mkdir(parents=True, exist_ok=True)

(data / "installed.json").write_text(
    json.dumps(installed, indent=2) + "\n",
    encoding="utf-8"
)
PY

cat > "$BIN_DIR/tbox" <<EOF2
#!/data/data/com.termux/files/usr/bin/bash
set -eu
export TBOX_HOME="$INSTALL_DIR"
export PYTHONPATH="\$TBOX_HOME\${PYTHONPATH:+:\$PYTHONPATH}"
exec python "\$TBOX_HOME/main.py" "\$@"
EOF2

chmod 755 "$BIN_DIR/tbox"

say "Installation complete."
say "Run: tbox"
say "Run diagnostics: tbox doctor"
say "Update: bash $INSTALL_DIR/update.sh"
