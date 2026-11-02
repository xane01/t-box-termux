#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
INSTALL_DIR="${TBOX_HOME:-$HOME/.local/opt/t-box-termux}"
if [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "Git installation not found: $INSTALL_DIR"
  echo "For the first install, run install.sh from the repository."
  exit 1
fi
git -C "$INSTALL_DIR" pull --ff-only
echo "T-BOX source updated. Run 'tbox doctor' to verify."
