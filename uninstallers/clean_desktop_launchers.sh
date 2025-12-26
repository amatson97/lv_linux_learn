#!/bin/bash
# Description: Remove desktop launchers and helper scripts created by lv_linux_learn
#
# Cleans up desktop shortcuts, helper scripts, and menu entries created by
# the lv_linux_learn installation scripts. Removes launchers from Desktop,
# Applications menu, and ~/.lv_connect helper directory for clean system restoration.
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
    green_echo "[*] Cleaning desktop launchers and helper scripts..."
    
    # Remove desktop icons
    green_echo "[*] Removing desktop icons..."
    rm -f "$HOME/Desktop/ShowZerotierInfo.desktop"
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
