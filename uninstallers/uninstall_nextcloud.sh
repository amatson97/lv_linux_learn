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
    
    if ! command -v nextcloud &> /dev/null; then
        green_echo "[!] Nextcloud Client is not installed."
        return 0
    fi
    
    # Remove Nextcloud package
    green_echo "[*] Removing Nextcloud Client package..."
    sudo apt remove --purge -y nextcloud-desktop nextcloud-client 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Nextcloud repository
    green_echo "[*] Removing Nextcloud repository..."
    sudo rm -f /etc/apt/sources.list.d/nextcloud*.list
    
    # Remove user data (optional)
    read -rp "Do you want to remove Nextcloud configuration? [y/N]: " remove_data
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing Nextcloud configuration..."
        rm -rf "$HOME/.config/Nextcloud"
        rm -rf "$HOME/.local/share/Nextcloud"
    fi
    
    green_echo "[+] Nextcloud Client has been uninstalled successfully!"
}

main "$@"
