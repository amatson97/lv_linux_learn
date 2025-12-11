#!/bin/bash
# Uninstall NordVPN
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Uninstalling NordVPN..."
    
    if ! command -v nordvpn &> /dev/null; then
        green_echo "[!] NordVPN is not installed."
        return 0
    fi
    
    # Disconnect and logout
    green_echo "[*] Disconnecting and logging out..."
    nordvpn disconnect 2>/dev/null || true
    nordvpn logout 2>/dev/null || true
    nordvpn set meshnet off 2>/dev/null || true
    
    # Remove packages
    green_echo "[*] Removing NordVPN packages..."
    sudo apt remove --purge -y nordvpn nordvpn-gui 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove repository
    green_echo "[*] Removing NordVPN repository..."
    sudo rm -f /etc/apt/sources.list.d/nordvpn.list
    sudo apt update
    
    # Remove user from nordvpn group
    green_echo "[*] Removing user from nordvpn group..."
    sudo deluser "$USER" nordvpn 2>/dev/null || true
    sudo groupdel nordvpn 2>/dev/null || true
    
    # Remove desktop icons
    green_echo "[*] Removing desktop icons..."
    rm -f "$HOME/Desktop/ShowMeshnetInfo.desktop"
    rm -f "$HOME/Desktop/ShowNordVPNInfo.desktop"
    rm -f "$HOME/.lv_connect/ShowMeshnetInfo.sh"
    
    green_echo "[+] NordVPN has been uninstalled successfully!"
    green_echo "[!] You may need to reboot to fully remove group membership."
}

main "$@"
