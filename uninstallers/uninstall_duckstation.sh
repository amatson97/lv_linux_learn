#!/usr/bin/env bash
# Description: Uninstall DuckStation PS1 emulator and remove desktop integration

set -euo pipefail

# Source shared helpers
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

APPIMAGE_DIR="$HOME/Applications"
APPIMAGE_NAME="DuckStation-x64.AppImage"
DESKTOP_FILE="$HOME/.local/share/applications/duckstation.desktop"
ICON_FILE="$HOME/.local/share/icons/duckstation.png"

green_echo "Uninstalling DuckStation..."

# Remove AppImage
if [[ -f "$APPIMAGE_DIR/$APPIMAGE_NAME" ]]; then
    rm -f "$APPIMAGE_DIR/$APPIMAGE_NAME"
    green_echo "Removed AppImage"
else
    green_echo "AppImage not found"
fi

# Remove desktop integration
if [[ -f "$DESKTOP_FILE" ]]; then
    rm -f "$DESKTOP_FILE"
    green_echo "Removed desktop file"
fi

# Remove icon
if [[ -f "$ICON_FILE" ]]; then
    rm -f "$ICON_FILE"
    green_echo "Removed icon"
fi

# Update desktop database
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

green_echo "DuckStation uninstalled successfully!"
green_echo "Note: User data remains in ~/.local/share/duckstation/ and ~/.config/duckstation/"
