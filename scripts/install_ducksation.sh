#!/usr/bin/env bash
# Description: Install DuckStation PS1 emulator as AppImage with desktop integration
# Another change 2

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
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$ICON_DIR"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/pixmaps"

green_echo "Setting up DuckStation integration..."

# Create wrapper script for X11/Wayland compatibility
WRAPPER_SCRIPT="$APPIMAGE_DIR/duckstation-launcher.sh"
cat > "$WRAPPER_SCRIPT" << 'WRAPPER_EOF'
#!/usr/bin/env bash
# DuckStation launcher with X11/Wayland support

APPIMAGE_DIR="$HOME/Applications"
APPIMAGE_NAME="DuckStation-x64.AppImage"

# Set up environment for better Wayland/X11 compatibility
export XDG_SESSION_TYPE="${XDG_SESSION_TYPE:-x11}"

# For Qt applications on Wayland, set QT_QPA_PLATFORM if needed
if [[ "$XDG_SESSION_TYPE" == "wayland" ]]; then
    # Try native Wayland first, fallback to XWayland if issues occur
    export QT_QPA_PLATFORM="wayland"
    export QT_QPA_PLATFORM_PLUGIN_PATH="/usr/lib/x86_64-linux-gnu/qt5/plugins"
fi

# Run the AppImage
exec "$APPIMAGE_DIR/$APPIMAGE_NAME" "$@"
WRAPPER_EOF

chmod +x "$WRAPPER_SCRIPT"
green_echo "Created launcher wrapper for X11/Wayland support"

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

cd "$TMP_DIR"
cp "$APPIMAGE_DIR/$APPIMAGE_NAME" "$TMP_DIR/"
green_echo "Extracting AppImage contents..."
./"$APPIMAGE_NAME" --appimage-extract > /dev/null 2>&1 || true

# Try to find icon in multiple locations
ICON_FILE=""
ICON_NAME=""
if [[ -d "squashfs-root" ]]; then
    green_echo "Searching for icons in AppImage..."
    # Try 512x512 first (highest quality)
    ICON_FILE=$(find squashfs-root -path "*512x512*" -name "*.png" 2>/dev/null | head -1)
    # Try any high-res icon
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" -size +50k 2>/dev/null | grep -iE "(duck|logo)" | head -1)
    # Try common icon paths
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/pixmaps/*" -name "*.png" 2>/dev/null | head -1)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/icons/*" -name "*.png" 2>/dev/null | head -1)
    # Generic fallback
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" 2>/dev/null | grep -v "lib" | head -1)
fi

# Extract and install icon if found
if [[ -f "$ICON_FILE" ]]; then
    green_echo "Found icon: $ICON_FILE"
    cp "$ICON_FILE" "$ICON_DIR/duckstation.png"
    cp "$ICON_FILE" "$HOME/.local/share/pixmaps/duckstation.png"
    ICON_NAME="$ICON_DIR/duckstation.png"
    green_echo "Icon installed to: $ICON_NAME"
else
    green_echo "Warning: Icon not found in AppImage, checking for fallbacks..."
    # If no icon found, try to get one from system or use path
    if [[ -f "/usr/share/icons/hicolor/256x256/apps/applications-games.png" ]]; then
        cp "/usr/share/icons/hicolor/256x256/apps/applications-games.png" "$ICON_DIR/duckstation.png"
        ICON_NAME="$ICON_DIR/duckstation.png"
    else
        ICON_NAME="applications-games"
    fi
fi

# Create desktop file with absolute icon path
cat > "$DESKTOP_TARGET" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DuckStation
Exec=$WRAPPER_SCRIPT
Icon=$ICON_NAME
Comment=Fast PlayStation 1 Emulator
GenericName=Emulator
Categories=Game;Emulator;
Keywords=ps1;playstation;duckstation;emulator;
StartupWMClass=AppRun.wrapped
Terminal=false
X-AppImage-Version=latest
EOF

chmod 644 "$DESKTOP_TARGET"

# Mark desktop file as trusted for GNOME
green_echo "Marking desktop file as trusted..."
gio set "$DESKTOP_TARGET" metadata::trusted true 2>/dev/null || true

# Validate desktop file syntax
if command -v desktop-file-validate &> /dev/null; then
    desktop-file-validate "$DESKTOP_TARGET" || green_echo "Desktop file has warnings (non-critical)"
fi

# Update icon and desktop caches
green_echo "Updating icon and desktop caches..."
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true

# Clear and rebuild all icon caches
for theme_dir in "$HOME/.local/share/icons"/*; do
    [[ -d "$theme_dir" ]] && gtk-update-icon-cache -t -f "$theme_dir" 2>/dev/null || true
done
gtk-update-icon-cache -t -f "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
gtk-update-icon-cache -t "$HOME/.local/share/pixmaps/" 2>/dev/null || true

# Clear GNOME caches
green_echo "Clearing GNOME Shell caches..."
rm -rf "$HOME/.cache/gnome-shell/" 2>/dev/null || true
rm -rf "$HOME/.cache/evolution/shell/" 2>/dev/null || true
rm -rf "$HOME/.local/share/recently-used.xbel" 2>/dev/null || true

# Force GNOME to reload applications
if command -v gsettings &> /dev/null; then
    green_echo "Reloading GNOME application cache..."
    gsettings reset org.gnome.desktop.app-folders folder-children 2>/dev/null || true
fi

green_echo "DuckStation integrated to GNOME launcher!"
green_echo ""
green_echo "Note: If icon doesn't appear in launcher/sidebar, please:"
green_echo "  1. Press Alt+F2, type 'r' and press Enter to restart GNOME Shell"
green_echo "  2. Or log out and log back in"
green_echo "  3. Launch DuckStation from search, then check sidebar"

green_echo "Done! Launch from menu or $APPIMAGE_DIR/$APPIMAGE_NAME"
