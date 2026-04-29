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
APPIMAGE_URL="https://github.com/stenzek/duckstation/releases/latest/download/$APPIMAGE_NAME"
ICON_THEME_NAME="duckstation"

detect_desktop_env() {
    local de="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-}}"
    de="$(echo "$de" | tr '[:upper:]' '[:lower:]')"

    if [[ "$de" == *"kde"* || "$de" == *"plasma"* ]]; then
        echo "kde"
    elif [[ "$de" == *"gnome"* ]]; then
        echo "gnome"
    else
        echo "other"
    fi
}

is_valid_appimage() {
    local file_path="$1"
    [[ -f "$file_path" ]] || return 1
    # AppImage files are ELF binaries; verify magic bytes to avoid cached HTML/404 files.
    local magic
    magic=$(head -c 4 "$file_path" | od -An -tx1 | tr -d ' \n')
    [[ "$magic" == "7f454c46" ]]
}

download_appimage() {
    green_echo "Downloading DuckStation..."
    if command -v curl &> /dev/null; then
        curl -fL --retry 3 --retry-delay 2 -o "$APPIMAGE_NAME" "$APPIMAGE_URL"
    else
        wget -O "$APPIMAGE_NAME" "$APPIMAGE_URL"
    fi
    chmod +x "$APPIMAGE_NAME"
}

install_icon_asset() {
    local source_icon="$1"
    local extension="${source_icon##*.}"
    local lower_extension
    lower_extension="$(echo "$extension" | tr '[:upper:]' '[:lower:]')"

    mkdir -p "$HOME/.local/share/pixmaps"

    if [[ "$lower_extension" == "svg" ]]; then
        local scalable_dir="$HOME/.local/share/icons/hicolor/scalable/apps"
        mkdir -p "$scalable_dir"
        cp "$source_icon" "$scalable_dir/$ICON_THEME_NAME.svg"
        cp "$source_icon" "$HOME/.local/share/pixmaps/$ICON_THEME_NAME.svg"
    else
        local png_dir="$HOME/.local/share/icons/hicolor/256x256/apps"
        mkdir -p "$png_dir"
        cp "$source_icon" "$png_dir/$ICON_THEME_NAME.png"
        cp "$source_icon" "$HOME/.local/share/pixmaps/$ICON_THEME_NAME.png"
    fi
}

mkdir -p "$APPIMAGE_DIR"
cd "$APPIMAGE_DIR"

if ! is_valid_appimage "$APPIMAGE_NAME"; then
    if [[ -f "$APPIMAGE_NAME" ]]; then
        green_echo "Existing DuckStation file is invalid, re-downloading..."
        rm -f "$APPIMAGE_NAME"
    fi
    download_appimage
fi

if ! is_valid_appimage "$APPIMAGE_NAME"; then
    green_echo "Error: Downloaded file is not a valid AppImage."
    green_echo "Please check: https://github.com/stenzek/duckstation/releases/latest"
    exit 1
fi

# Extract for integration if not done
DESKTOP_TARGET="$HOME/.local/share/applications/duckstation.desktop"
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
# For Qt applications on Wayland, prefer Wayland but allow XWayland fallback.
if [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland;xcb}"
fi

# Run the AppImage
exec "$APPIMAGE_DIR/$APPIMAGE_NAME" "$@"
WRAPPER_EOF

chmod +x "$WRAPPER_SCRIPT"
green_echo "Created launcher wrapper for X11/Wayland support"

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
cp "$APPIMAGE_DIR/$APPIMAGE_NAME" "$TMP_DIR/"
green_echo "Extracting AppImage contents..."
./"$APPIMAGE_NAME" --appimage-extract > /dev/null 2>&1 || true

# Try to find icon in multiple locations
ICON_FILE=""
ICON_NAME="$ICON_THEME_NAME"
if [[ -d "squashfs-root" ]]; then
    green_echo "Searching for icons in AppImage..."
    ICON_FILE=$(find squashfs-root -name ".DirIcon" 2>/dev/null | head -1)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/icons/*" -name "*.svg" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)
    # Try 512x512 first (highest quality)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*512x512*" -name "*.png" 2>/dev/null | head -1)
    # Try any high-res icon
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" -size +50k 2>/dev/null | grep -iE "(duck|logo)" | head -1)
    # Try common icon paths
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/pixmaps/*" -name "*.png" 2>/dev/null | head -1)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/icons/*" -name "*.png" 2>/dev/null | head -1)
    # Generic fallback
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" 2>/dev/null | grep -v "lib" | head -1)
    [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.svg" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)
fi

# Extract and install icon if found
if [[ -f "$ICON_FILE" ]]; then
    green_echo "Found icon: $ICON_FILE"
    install_icon_asset "$ICON_FILE"
    green_echo "Icon installed as theme icon: $ICON_NAME"
else
    green_echo "Warning: Icon not found in AppImage, checking for fallbacks..."
    # If no icon found, try to get one from system or use theme fallback
    if [[ -f "/usr/share/icons/hicolor/256x256/apps/applications-games.png" ]]; then
        install_icon_asset "/usr/share/icons/hicolor/256x256/apps/applications-games.png"
    else
        ICON_NAME="applications-games"
    fi
fi

# Create desktop file using the icon theme name so KDE/Plasma can resolve it reliably.
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

# Ensure no desktop shortcut is created; launcher entry lives in the app menu only.
rm -f "$HOME/Desktop/DuckStation.desktop" 2>/dev/null || true
rm -f "$HOME/Desktop/duckstation.desktop" 2>/dev/null || true

DE_TYPE="$(detect_desktop_env)"

# Mark desktop file as trusted where supported (primarily GNOME environments)
if command -v gio &> /dev/null; then
    green_echo "Marking desktop file as trusted..."
    gio set "$DESKTOP_TARGET" metadata::trusted true 2>/dev/null || true
fi

# Validate desktop file syntax
if command -v desktop-file-validate &> /dev/null; then
    desktop-file-validate "$DESKTOP_TARGET" || green_echo "Desktop file has warnings (non-critical)"
fi

# Update icon and desktop caches
green_echo "Updating icon and desktop caches..."
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true
xdg-desktop-menu forceupdate 2>/dev/null || true

# Clear and rebuild all icon caches
for theme_dir in "$HOME/.local/share/icons"/*; do
    [[ -d "$theme_dir" ]] && gtk-update-icon-cache -t -f "$theme_dir" 2>/dev/null || true
done
gtk-update-icon-cache -t -f "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
gtk-update-icon-cache -t "$HOME/.local/share/pixmaps/" 2>/dev/null || true

if [[ "$DE_TYPE" == "gnome" ]]; then
    # GNOME-specific refresh
    green_echo "Refreshing GNOME launcher cache..."
    rm -rf "$HOME/.cache/gnome-shell/" 2>/dev/null || true
    if command -v gsettings &> /dev/null; then
        gsettings reset org.gnome.desktop.app-folders folder-children 2>/dev/null || true
    fi
elif [[ "$DE_TYPE" == "kde" ]]; then
    # KDE/Plasma cache refresh (Kubuntu)
    green_echo "Refreshing KDE launcher cache..."
    if command -v kbuildsycoca6 &> /dev/null; then
        kbuildsycoca6 --noincremental 2>/dev/null || true
    elif command -v kbuildsycoca5 &> /dev/null; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
    fi
fi

green_echo "DuckStation integrated to your application launcher!"
green_echo ""
green_echo "If icon does not appear immediately, log out and back in."

green_echo "Done! Launch from menu or $APPIMAGE_DIR/$APPIMAGE_NAME"
