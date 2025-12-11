#!/bin/bash
# Clean Desktop Launchers and Helper Scripts
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Cleaning desktop launchers and helper scripts..."
    
    # Remove desktop icons
    green_echo "[*] Removing desktop icons..."
    rm -f "$HOME/Desktop/ZeroTierInfo.desktop"
    rm -f "$HOME/Desktop/ShowMeshnetInfo.desktop"
    rm -f "$HOME/Desktop/ShowNordVPNInfo.desktop"
    rm -f "$HOME/Desktop/ShowHamachiInfo.desktop"
    rm -f "$HOME/Desktop/RemoteDesktopInfo.desktop"
    
    # Remove helper scripts
    if [[ -d "$HOME/.lv_connect" ]]; then
        green_echo "[*] Removing helper scripts directory..."
        rm -rf "$HOME/.lv_connect"
    fi
    
    # Count removed items
    green_echo "[+] Desktop launchers and helper scripts have been cleaned!"
}

main "$@"
