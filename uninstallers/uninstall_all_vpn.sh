#!/bin/bash
# Uninstall All VPN Tools
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Uninstalling all VPN tools..."
    echo ""
    echo "This will remove:"
    echo "  - ZeroTier VPN"
    echo "  - NordVPN"
    echo "  - LogMeIn Hamachi"
    echo ""
    read -rp "Are you sure you want to continue? [y/N]: " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        green_echo "[*] Uninstall cancelled."
        return 0
    fi
    
    # Uninstall ZeroTier
    if command -v zerotier-cli &> /dev/null; then
        green_echo ""
        green_echo "[*] ========== Uninstalling ZeroTier =========="
        bash "$script_dir/uninstall_zerotier.sh"
    fi
    
    # Uninstall NordVPN
    if command -v nordvpn &> /dev/null; then
        green_echo ""
        green_echo "[*] ========== Uninstalling NordVPN =========="
        bash "$script_dir/uninstall_nordvpn.sh"
    fi
    
    # Uninstall Hamachi
    if command -v hamachi &> /dev/null; then
        green_echo ""
        green_echo "[*] ========== Uninstalling Hamachi =========="
        # Logout and leave networks
        sudo hamachi logout 2>/dev/null || true
        
        # Remove package
        green_echo "[*] Removing Hamachi package..."
        sudo apt remove --purge -y logmein-hamachi 2>/dev/null || true
        sudo apt autoremove -y
        
        # Remove configuration
        sudo rm -rf /var/lib/logmein-hamachi
        sudo rm -f /etc/init.d/logmein-hamachi
        
        # Remove desktop icons
        rm -f "$HOME/Desktop/ShowHamachiInfo.desktop"
        rm -f "$HOME/.lv_connect/ShowHamachiInfo.sh"
        
        green_echo "[+] Hamachi has been uninstalled successfully!"
    fi
    
    green_echo ""
    green_echo "[+] All VPN tools have been uninstalled!"
}

main "$@"
