#!/bin/bash
# Description: Remove Wine Windows compatibility layer and prefix data
#
# Uninstalls Wine and Winetricks with complete removal of Windows application
# compatibility layer. Cleans up wine prefixes, installed Windows software,
# and system integration while preserving or removing Windows app data.
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
    green_echo "[*] Uninstalling Wine..."
    
    if ! command -v wine &> /dev/null; then
        green_echo "[!] Wine is not installed."
        return 0
    fi
    
    # Remove Wine packages
    green_echo "[*] Removing Wine packages..."
    sudo apt remove --purge -y wine* winetricks 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Wine repository (if added)
    green_echo "[*] Removing Wine repository..."
    sudo rm -f /etc/apt/sources.list.d/winehq*.list
    
    # Remove user data (optional)
    read -rp "Do you want to remove Wine prefix data (~/.wine)? [y/N]: " remove_data
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing Wine prefix data..."
        rm -rf "$HOME/.wine"
    fi
    
    green_echo "[+] Wine has been uninstalled successfully!"
}

main "$@"
