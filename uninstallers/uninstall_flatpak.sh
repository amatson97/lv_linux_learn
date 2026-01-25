#!/bin/bash
# Description: Remove Flatpak system and all installed applications
#
# Completely removes Flatpak universal package system, all installed
# Flatpak applications (including Flatseal), repositories (including Flathub),
# and cleans up user data. Provides comprehensive cleanup of the entire
# Flatpak ecosystem.
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
    green_echo "[*] Uninstalling Flatpak..."
    
    if ! command -v flatpak &> /dev/null; then
        green_echo "[!] Flatpak is not installed."
        return 0
    fi
    
    # List installed flatpaks
    green_echo "[*] Listing installed Flatpak applications..."
    flatpak list 2>/dev/null || true
    
    echo ""
    if confirm_action "Do you want to remove all Flatpak applications?\n\nThis will uninstall all Flatpak apps (including Flatseal) before removing Flatpak itself." "Remove Flatpak Apps"; then
        remove_apps="y"
    else
        remove_apps="n"
    fi
    if [[ "$remove_apps" =~ ^[Yy]$ ]]; then
        # Remove Flatseal first if installed
        if flatpak list --app | grep -q "com.github.tchx84.Flatseal"; then
            green_echo "[*] Removing Flatseal..."
            flatpak uninstall -y com.github.tchx84.Flatseal 2>/dev/null || true
        fi
        
        green_echo "[*] Removing all remaining Flatpak applications..."
        flatpak uninstall --all -y 2>/dev/null || true
    fi
    
    # Remove Flatpak package
    green_echo "[*] Removing Flatpak package..."
    sudo apt remove --purge -y flatpak gnome-software-plugin-flatpak 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Flatpak data
    green_echo "[*] Removing Flatpak data directories..."
    rm -rf "$HOME/.local/share/flatpak"
    sudo rm -rf /var/lib/flatpak
    
    green_echo "[+] Flatpak has been uninstalled successfully!"
}

main "$@"
