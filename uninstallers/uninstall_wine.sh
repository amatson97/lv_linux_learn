#!/bin/bash
# Uninstall Wine
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

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
