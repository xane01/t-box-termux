#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
INSTALL_DIR="${TBOX_HOME:-$HOME/.local/opt/t-box-termux}"
BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
read -r -p "Remove T-BOX program files? User config/data will be preserved. [y/N]: " answer
case "${answer,,}" in
  y|yes)
    rm -rf "$INSTALL_DIR"
    rm -f "$BIN_DIR/tbox"
    echo "T-BOX program files removed. Config and user data were preserved."
    ;;
  *) echo "Cancelled." ;;
esac
