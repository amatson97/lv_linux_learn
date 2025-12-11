#!/bin/bash
# Uninstall Nextcloud Client
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

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
