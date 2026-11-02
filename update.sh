#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

INSTALL_DIR="${TBOX_HOME:-$HOME/.local/opt/t-box-termux}"

if [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "Git installation not found: $INSTALL_DIR"
  echo "Run install.sh to install T-BOX."
  exit 1
fi

echo "[T-BOX] Checking repository status..."

if [ -n "$(git -C "$INSTALL_DIR" status --porcelain)" ]; then
  echo "Local changes detected. Update cancelled to protect your changes."
  exit 1
fi

echo "[T-BOX] Fetching updates..."
git -C "$INSTALL_DIR" pull --ff-only

echo "[T-BOX] Update completed."
echo "[T-BOX] Run: tbox doctor"
