#!/bin/bash
# Description: Remove Nextcloud Desktop Client with sync data options
#
# Uninstalls Nextcloud Desktop Client and provides options for handling
# synchronized data. Removes Flatpak package, cleans up sync folders,
# and offers to preserve or remove local file synchronization data.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES_DIR="$SCRIPT_DIR/../includes"
if [ -f "$INCLUDES_DIR/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$INCLUDES_DIR/main.sh"
elif [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$HOME/lv_linux_learn/includes/main.sh"
else
    echo "Error: Could not find includes/main.sh"
    exit 1
fi

main() {
    green_echo "[*] Uninstalling Nextcloud Client..."
    
    # Detect installation method: apt package or Flatpak
    apt_installed=false
    flatpak_installed=false

    # Keep identifiers in variables to match installer
    APP_ID="com.nextcloud.desktopclient.nextcloud"
    DESKTOP_DB_PATH="/var/lib/flatpak/exports/share/applications"

    if command -v dpkg >/dev/null 2>&1; then
        if dpkg -s nextcloud-desktop >/dev/null 2>&1 || dpkg -s nextcloud-client >/dev/null 2>&1; then
            apt_installed=true
        fi
    fi

    if command -v flatpak >/dev/null 2>&1; then
        if flatpak list 2>/dev/null | grep -q "$APP_ID"; then
            flatpak_installed=true
        fi
    fi

    if [ "$apt_installed" = false ] && [ "$flatpak_installed" = false ]; then
        green_echo "[!] Nextcloud Client is not installed."
        return 0
    fi
    
    # Remove Nextcloud package (apt) if present
    if [ "$apt_installed" = true ]; then
        green_echo "[*] Removing Nextcloud Client package (apt)..."
        sudo apt remove --purge -y nextcloud-desktop nextcloud-client 2>/dev/null || true
        sudo apt autoremove -y
    fi
    
    # Remove Nextcloud repository
    green_echo "[*] Removing Nextcloud repository..."
    sudo rm -f /etc/apt/sources.list.d/nextcloud*.list

    # Remove Flatpak package if present
    if [ "$flatpak_installed" = true ]; then
        green_echo "[*] Removing Nextcloud Flatpak package..."
        # Run uninstall and filter out harmless dbus-launch error messages that can
        # appear when `dbus-launch`/X11 helpers are not present in minimal envs.
        flatpak_output="$(sudo flatpak uninstall -y --delete-data "$APP_ID" 2>&1 || true)"
        # Print output but remove any lines mentioning dbus-launch to avoid noisy errors
        printf "%s\n" "$flatpak_output" | grep -v -i "dbus-launch" || true
        # Reset any overrides (e.g., /dev/shm override)
        sudo flatpak override --reset "$APP_ID" || true
        # Update desktop integration
        sudo update-desktop-database "$DESKTOP_DB_PATH" || true
    fi
    
    # Remove user data (optional)
    if confirm_action "Do you want to remove Nextcloud configuration?\n\nThis will delete saved accounts and settings." "Remove Nextcloud Config"; then
        remove_data="y"
    else
        remove_data="n"
    fi
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing Nextcloud configuration..."
        rm -rf "$HOME/.config/Nextcloud"
        rm -rf "$HOME/.local/share/Nextcloud"
    fi
    
    green_echo "[+] Nextcloud Client has been uninstalled successfully!"
}

main "$@"
