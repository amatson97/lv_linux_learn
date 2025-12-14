#!/bin/bash
# Uninstall Google Chrome
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
    green_echo "[*] Uninstalling Google Chrome..."
    
    if ! dpkg -l | grep -q google-chrome-stable; then
        green_echo "[!] Google Chrome is not installed."
        return 0
    fi
    
    # Remove Chrome package
    green_echo "[*] Removing Google Chrome package..."
    sudo apt remove --purge -y google-chrome-stable 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Chrome repository
    green_echo "[*] Removing Google Chrome repository..."
    sudo rm -f /etc/apt/sources.list.d/google-chrome.list
    
    # Remove user data (optional)
    read -rp "Do you want to remove Chrome user data? [y/N]: " remove_data
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing Chrome user data..."
        rm -rf "$HOME/.config/google-chrome"
        rm -rf "$HOME/.cache/google-chrome"
    fi
    
    green_echo "[+] Google Chrome has been uninstalled successfully!"
}

main "$@"
