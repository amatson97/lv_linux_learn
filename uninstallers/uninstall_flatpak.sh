#!/bin/bash
# Uninstall Flatpak
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
    read -rp "Do you want to remove all Flatpak applications? [y/N]: " remove_apps
    if [[ "$remove_apps" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing all Flatpak applications..."
        flatpak uninstall --all -y 2>/dev/null || true
    fi
    
    # Remove Flatpak package
    green_echo "[*] Removing Flatpak package..."
    sudo apt remove --purge -y flatpak 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Flatpak data
    green_echo "[*] Removing Flatpak data directories..."
    rm -rf "$HOME/.local/share/flatpak"
    sudo rm -rf /var/lib/flatpak
    
    green_echo "[+] Flatpak has been uninstalled successfully!"
}

main "$@"
