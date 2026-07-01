#!/usr/bin/env bash
# Description: Install DuckStation PS1 emulator as AppImage with desktop integration
#
# Usage:
#   ./install_duckstation.sh                    # Install latest version
#   APPIMAGE_DIR=/custom/path ./install_duckstation.sh  # Custom install location
#   DUCKSTATION_VERSION=0.1-23456 ./install_duckstation.sh  # Specific version

set -euo pipefail

# Source shared helpers
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Configuration - allow environment variable override for installation directory and version
APPIMAGE_DIR="${APPIMAGE_DIR:-$HOME/Applications}"
APPIMAGE_NAME="DuckStation-x64.AppImage"
ICON_THEME_NAME="duckstation"

# Version pinning support
DUCKSTATION_VERSION="${DUCKSTATION_VERSION:-latest}"

# Build download URL based on version
if [[ "$DUCKSTATION_VERSION" == "latest" ]]; then
    APPIMAGE_URL="https://github.com/stenzek/duckstation/releases/latest/download/$APPIMAGE_NAME"
else
    # Version format: 0.1-23456 or v0.1-23456
    local version_clean="${DUCKSTATION_VERSION#v}"
    APPIMAGE_URL="https://github.com/stenzek/duckstation/releases/download/$version_clean/$APPIMAGE_NAME"
fi

# Check for required dependencies
check_dependencies() {
    local missing_deps=()
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        missing_deps+=("curl or wget")
    fi
    if ! command -v tar &> /dev/null; then
        missing_deps+=("tar")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        green_echo "Error: Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
}

# Validate installation directory and create if needed
validate_installation_directory() {
    local dir="$APPIMAGE_DIR"

    # Create directory if it doesn't exist
    mkdir -p "$dir" || {
        green_echo "Error: Failed to create installation directory $dir"
        exit 1
    }

    # Check if we can write to the directory
    if [[ ! -w "$dir" ]]; then
        green_echo "Error: No write permission for $dir"
        green_echo "Please ensure you have write access or run with appropriate permissions"
        exit 1
    fi

    cd "$dir" || {
        green_echo "Error: Failed to change to directory $dir"
        exit 1
    }
}

# Display usage information
show_usage() {
    cat << 'EOF'
DuckStation Installer - Fast PlayStation 1 Emulator

Usage:
  ./install_duckstation.sh                    # Install latest version
  APPIMAGE_DIR=/custom/path ./install_duckstation.sh  # Custom install location
  DUCKSTATION_VERSION=0.1-23456 ./install_duckstation.sh  # Specific version

Environment Variables:
  APPIMAGE_DIR        Installation directory (default: $HOME/Applications)
  DUCKSTATION_VERSION Version to install (default: latest)

Examples:
  # Install latest version
  ./install_duckstation.sh

  # Install specific version
  DUCKSTATION_VERSION=0.1-23456 ./install_duckstation.sh

  # Custom installation directory
  APPIMAGE_DIR=/opt/emulators ./install_duckstation.sh

After installation, you may need to restart your desktop environment (Alt+F2 → r)
or log out and back in for the launcher icon to appear.

EOF
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_usage
                exit 0
                ;;
            --version|-v)
                echo "DuckStation Installer"
                exit 0
                ;;
            *)
                green_echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

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

# Main execution flow
main() {
    # Parse command-line arguments first
    parse_args "$@"

    green_echo "Starting DuckStation installation..."
    if [[ "$DUCKSTATION_VERSION" != "latest" ]]; then
        green_echo "Installing version: $DUCKSTATION_VERSION"
    fi

    # Check dependencies before proceeding
    check_dependencies

    # Validate and prepare installation directory
    validate_installation_directory

    # Download or verify AppImage
    if ! is_valid_appimage "$APPIMAGE_NAME"; then
        if [[ -f "$APPIMAGE_NAME" ]]; then
            green_echo "Existing DuckStation file is invalid, re-downloading..."
            rm -f "$APPIMAGE_NAME"
        fi
        download_appimage

        # Verify the downloaded file
        if ! is_valid_appimage "$APPIMAGE_NAME"; then
            green_echo "Error: Downloaded file is not a valid AppImage."
            green_echo "Please check: $APPIMAGE_URL"
            exit 1
        fi
    else
        green_echo "Using existing DuckStation installation at $APPIMAGE_DIR/$APPIMAGE_NAME"
    fi

    # Set up desktop integration
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

    # Extract AppImage to find icon (use temporary directory)
    TMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TMP_DIR"' EXIT

    cd "$TMP_DIR" || {
        green_echo "Error: Failed to enter temporary directory"
        exit 1
    }

    cp "$APPIMAGE_DIR/$APPIMAGE_NAME" "$TMP_DIR/"
    green_echo "Extracting AppImage contents..."
    if ! ./"$APPIMAGE_NAME" --appimage-extract > /dev/null 2>&1; then
        green_echo "Warning: Failed to extract AppImage (icon extraction may fail)"
    fi

    # Try to find icon in multiple locations with improved search strategy
    ICON_FILE=""
    ICON_NAME="$ICON_THEME_NAME"

    if [[ -d "squashfs-root" ]]; then
        green_echo "Searching for icons in AppImage..."
        # Search strategy: prioritize high-quality icons first
        ICON_FILE=$(find squashfs-root -path "*512x512*" -name "*.png" 2>/dev/null | head -1)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*256x256*" -name "*.png" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name ".DirIcon" 2>/dev/null | head -1)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/icons/*" -name "*.svg" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/pixmaps/*" -name "*.png" 2>/dev/null | head -1)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -path "*/icons/*" -name "*.png" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)

        # Fallback: try any PNG larger than 50KB (likely an icon)
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.png" -size +50k 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)

        # Final fallback: any SVG with duck/station in name
        [[ -z "$ICON_FILE" ]] && ICON_FILE=$(find squashfs-root -name "*.svg" 2>/dev/null | grep -iE "(duck|station|logo)" | head -1)
    fi

    # Extract and install icon if found, with external fallback support
    if [[ -f "$ICON_FILE" ]]; then
        green_echo "Found icon: $ICON_FILE"
        install_icon_asset "$ICON_FILE"
        green_echo "Icon installed as theme icon: $ICON_NAME"
    else
        green_echo "Warning: Icon not found in AppImage, checking for external fallbacks..."

        # Try to download a fallback icon from DuckStation's GitHub repository
        local FALLBACK_ICON_URL="https://raw.githubusercontent.com/stenzek/duckstation/master/resources/duckstation.svg"
        local FALLBACK_ICON_PATH="$TMP_DIR/duckstation-fallback.svg"

        if command -v curl &> /dev/null; then
            if curl -fL --retry 2 --retry-delay 1 -o "$FALLBACK_ICON_PATH" "$FALLBACK_ICON_URL" 2>/dev/null; then
                install_icon_asset "$FALLBACK_ICON_PATH"
                green_echo "Downloaded fallback icon from DuckStation repository"
            fi
        elif command -v wget &> /dev/null; then
            if wget -qO "$FALLBACK_ICON_PATH" "$FALLBACK_ICON_URL" 2>/dev/null; then
                install_icon_asset "$FALLBACK_ICON_PATH"
                green_echo "Downloaded fallback icon from DuckStation repository"
            fi
        fi

        # System fallback if external download fails
        if [[ ! -f "$FALLBACK_ICON_PATH" || ! -s "$FALLBACK_ICON_PATH" ]]; then
            if [[ -f "/usr/share/icons/hicolor/256x256/apps/applications-games.png" ]]; then
                install_icon_asset "/usr/share/icons/hicolor/256x256/apps/applications-games.png"
            else
                ICON_NAME="applications-games"
                green_echo "Using system default icon: $ICON_NAME"
            fi
        fi
    fi

    # Create desktop file with improved metadata and version information
    local DESKTOP_VERSION="$DUCKSTATION_VERSION"
    if [[ "$DUCKSTATION_VERSION" == "latest" ]]; then
        DESKTOP_VERSION="$(date +%Y.%m.%d)"
    fi

    cat > "$DESKTOP_TARGET" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DuckStation
GenericName=PlayStation Emulator
Comment=Fast and accurate PlayStation 1 emulator
Exec=$WRAPPER_SCRIPT %F
Icon=$ICON_NAME
TryExec=$WRAPPER_SCRIPT
StartupWMClass=AppRun.wrapped
Terminal=false
Categories=Game;Emulator;
Keywords=PS1;PlayStation;Sony;Console;Emulation;
MimeType=application/x-psx-exe;
X-AppImage-Version=$DESKTOP_VERSION
EOF

    chmod 644 "$DESKTOP_TARGET"

    # Ensure no desktop shortcut is created (clean up any existing ones)
    rm -f "$HOME/Desktop/DuckStation.desktop" 2>/dev/null || true
    rm -f "$HOME/Desktop/duckstation.desktop" 2>/dev/null || true

    # Detect desktop environment for targeted cache updates
    local DE_TYPE="$(detect_desktop_env)"

    # Mark desktop file as trusted where supported (primarily GNOME environments)
    if command -v gio &> /dev/null; then
        green_echo "Marking desktop file as trusted..."
        if ! gio set "$DESKTOP_TARGET" metadata::trusted true 2>/dev/null; then
            green_echo "Warning: Failed to mark desktop file as trusted"
        fi
    fi

    # Validate desktop file syntax
    if command -v desktop-file-validate &> /dev/null; then
        if ! desktop-file-validate "$DESKTOP_TARGET" 2>/dev/null; then
            green_echo "Desktop file has warnings (non-critical)"
        fi
    fi

    # Update icon and desktop caches with better error handling
    green_echo "Updating icon and desktop caches..."
    local cache_updated=false

    if command -v update-desktop-database &> /dev/null; then
        if update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null; then
            cache_updated=true
        fi
    fi

    if command -v xdg-desktop-menu &> /dev/null; then
        if xdg-desktop-menu forceupdate 2>/dev/null; then
            cache_updated=true
        fi
    fi

    # Clear and rebuild all icon caches (only if tools are available)
    if command -v gtk-update-icon-cache &> /dev/null; then
        for theme_dir in "$HOME/.local/share/icons"/*; do
            [[ -d "$theme_dir" ]] && gtk-update-icon-cache -t -f "$theme_dir" 2>/dev/null || true
        done

        if [[ -d "$HOME/.local/share/icons/hicolor/" ]]; then
            gtk-update-icon-cache -t -f "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
        fi

        cache_updated=true
    fi

    # Desktop environment specific cache refresh
    if [[ "$DE_TYPE" == "gnome" ]]; then
        green_echo "Refreshing GNOME launcher cache..."
        rm -rf "$HOME/.cache/gnome-shell/" 2>/dev/null || true
        if command -v gsettings &> /dev/null; then
            gsettings reset org.gnome.desktop.app-folders folder-children 2>/dev/null || true
        fi
    elif [[ "$DE_TYPE" == "kde" ]]; then
        green_echo "Refreshing KDE launcher cache..."
        if command -v kbuildsycoca6 &> /dev/null; then
            kbuildsycoca6 --noincremental 2>/dev/null || true
        elif command -v kbuildsycoca5 &> /dev/null; then
            kbuildsycoca5 --noincremental 2>/dev/null || true
        fi
    fi

    # Final summary
    green_echo ""
    green_echo "✓ DuckStation successfully integrated to your application launcher!"
    if [[ "$cache_updated" == false ]]; then
        green_echo "Note: Some cache updates may require restarting your desktop environment"
    fi
    green_echo ""
    green_echo "You can launch DuckStation from:"
    green_echo "  - Your application menu (search for 'DuckStation')"
    green_echo "  - Directly via: $APPIMAGE_DIR/$APPIMAGE_NAME"
    green_echo ""

    if [[ "$DE_TYPE" == "gnome" || "$DE_TYPE" == "kde" ]]; then
        green_echo "For best results, restart your desktop environment or log out and back in."
    fi

    exit 0
}

# Execute main function with all arguments
main "$@"
