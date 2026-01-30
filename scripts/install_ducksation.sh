#!/usr/bin/env bash
# Description: Install DuckStation PS1 emulator as AppImage with desktop integration

set -euo pipefail

# Source shared helpers
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

APPIMAGE_DIR="$HOME/Applications"
APPIMAGE_NAME="DuckStation-x64.AppImage"
APPIMAGE_URL="https://github.com/stenzek/duckstation/releases/download/latest/$APPIMAGE_NAME"

mkdir -p "$APPIMAGE_DIR"
cd "$APPIMAGE_DIR"

if [[ ! -f "$APPIMAGE_NAME" ]]; then
    green_echo "Downloading DuckStation..."
    wget -O "$APPIMAGE_NAME" "$APPIMAGE_URL"
    chmod +x "$APPIMAGE_NAME"
fi

# Extract for integration if not done
DESKTOP_TARGET="$HOME/.local/share/applications/duckstation.desktop"
if [[ ! -f "$DESKTOP_TARGET" ]]; then
    green_echo "Extracting icon/desktop..."
    TMP_DIR=$(mktemp -d)
    cp "$APPIMAGE_NAME" "$TMP_DIR/"
    cd "$TMP_DIR"
    ./"$APPIMAGE_NAME" --appimage-extract > /dev/null 2>&1
    DESKTOP_FILE=$(find squashfs-root -name "duckstation*.desktop" | head -1)
    ICON_FILE=$(find squashfs-root -path "*512x512*" -name "*.png" | grep -i duckstation | head -1)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" | grep -i duck | head -1)

    # Ensure icons directory exists
    mkdir -p "$HOME/.local/share/icons"

    if [[ -f "$DESKTOP_FILE" ]]; then
        sed -i "s|Exec=.*|Exec=$APPIMAGE_DIR/$APPIMAGE_NAME|g; s|Icon=.*|Icon=$HOME/.local/share/icons/duckstation.png|g; s|Path=.*||g" "$DESKTOP_FILE"
        # Add StartupWMClass if not present
        if ! grep -q "^StartupWMClass=" "$DESKTOP_FILE"; then
            echo "StartupWMClass=duckstation-qt" >> "$DESKTOP_FILE"
        fi
        cp "$DESKTOP_FILE" "$DESKTOP_TARGET"
        chmod 644 "$DESKTOP_TARGET"
        [[ -f "$ICON_FILE" ]] && cp "$ICON_FILE" "$HOME/.local/share/icons/duckstation.png"
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
        green_echo "DuckStation integrated to GNOME launcher!"
    else
        # Fallback .desktop
        cat > "$DESKTOP_TARGET" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DuckStation
Exec=$APPIMAGE_DIR/$APPIMAGE_NAME
Icon=$HOME/.local/share/icons/duckstation.png
Comment=Fast PS1 Emulator
GenericName=Emulator
Categories=Game;Emulator;
Keywords=ps1;playstation;
StartupWMClass=duckstation-qt
EOF
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
        green_echo "Fallback shortcut created."
    fi
    rm -rf "$TMP_DIR"
else
    green_echo "Already installed."
fi

green_echo "Done! Launch from menu or $APPIMAGE_DIR/$APPIMAGE_NAME"
