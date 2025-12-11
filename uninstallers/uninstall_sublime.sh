#!/bin/bash
# Uninstall Sublime Text
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Uninstalling Sublime Text..."
    
    if ! dpkg -l | grep -q sublime-text; then
        green_echo "[!] Sublime Text is not installed."
        return 0
    fi
    
    # Remove Sublime Text package
    green_echo "[*] Removing Sublime Text package..."
    sudo apt remove --purge -y sublime-text 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Sublime Text repository
    green_echo "[*] Removing Sublime Text repository..."
    sudo rm -f /etc/apt/sources.list.d/sublime-text.list
    sudo rm -f /usr/share/keyrings/sublimehq-archive.gpg
    
    # Remove user data (optional)
    read -rp "Do you want to remove Sublime Text user data? [y/N]: " remove_data
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing Sublime Text user data..."
        rm -rf "$HOME/.config/sublime-text"
        rm -rf "$HOME/.config/sublime-text-3"
    fi
    
    green_echo "[+] Sublime Text has been uninstalled successfully!"
}

main "$@"
