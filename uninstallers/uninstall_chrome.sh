#!/bin/bash
# Uninstall Google Chrome
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

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
