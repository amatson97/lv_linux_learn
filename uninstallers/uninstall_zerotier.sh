#!/bin/bash
# Uninstall ZeroTier VPN
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Uninstalling ZeroTier VPN..."
    
    if ! command -v zerotier-cli &> /dev/null; then
        green_echo "[!] ZeroTier is not installed."
        return 0
    fi
    
    # Leave all networks before uninstalling
    green_echo "[*] Leaving all ZeroTier networks..."
    networks=$(sudo zerotier-cli listnetworks | tail -n +2 | awk '{print $3}')
    for network in $networks; do
        green_echo "[*] Leaving network: $network"
        sudo zerotier-cli leave "$network" 2>/dev/null || true
    done
    
    # Stop service
    green_echo "[*] Stopping ZeroTier service..."
    sudo systemctl stop zerotier-one 2>/dev/null || true
    sudo systemctl disable zerotier-one 2>/dev/null || true
    
    # Remove package
    green_echo "[*] Removing ZeroTier package..."
    sudo apt remove --purge -y zerotier-one 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove sudoers file
    green_echo "[*] Removing sudoers configuration..."
    sudo rm -f /etc/sudoers.d/zerotier-cli-nopasswd
    
    # Remove desktop icons
    green_echo "[*] Removing desktop icons..."
    rm -f "$HOME/Desktop/ZeroTierInfo.desktop"
    rm -f "$HOME/.lv_connect/ShowZeroTierInfo.sh"
    
    green_echo "[+] ZeroTier VPN has been uninstalled successfully!"
}

main "$@"
