#!/bin/bash
# Description: Remove all VPN software and restore network defaults
#
# Comprehensive VPN removal tool that uninstalls NordVPN, ZeroTier,
# and other VPN clients. Restores default network configuration,
# removes VPN-related services, and cleans up system modifications.
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
    green_echo "[*] Uninstalling all VPN tools..."
    echo ""
    echo "This will remove:"
    echo "  - ZeroTier VPN"
    echo "  - NordVPN"
    echo "  - LogMeIn Hamachi"
    echo ""
    
    # GUI confirmation using zenity if available (for menu.py compatibility)
    if command -v zenity &> /dev/null; then
        if ! zenity --question \
            --title="Confirm VPN Uninstall" \
            --text="This will uninstall all VPN tools:\n\n• ZeroTier VPN\n• NordVPN\n• LogMeIn Hamachi\n\nAre you sure you want to continue?" \
            --width=400 2>/dev/null; then
            green_echo "[*] Uninstall cancelled."
            return 0
        fi
    else
        green_echo "[!] WARNING: About to remove all VPN software!"
        green_echo "[*] Press Ctrl+C within 5 seconds to cancel..."
        sleep 5
    fi
    
    # Uninstall ZeroTier
    if command -v zerotier-cli &> /dev/null; then
        green_echo ""
        green_echo "[*] ========== Uninstalling ZeroTier =========="
        
        # Try to use dedicated script if available, otherwise inline uninstall
        if [ -f "$SCRIPT_DIR/uninstall_zerotier.sh" ]; then
            bash "$SCRIPT_DIR/uninstall_zerotier.sh"
        else
            # Inline ZeroTier uninstall logic
            green_echo "[*] Leaving all ZeroTier networks..."
            networks=$(sudo zerotier-cli listnetworks 2>/dev/null | tail -n +2 | awk '{print $3}' || true)
            for network in $networks; do
                green_echo "[*] Leaving network: $network"
                sudo zerotier-cli leave "$network" 2>/dev/null || true
            done
            
            green_echo "[*] Stopping ZeroTier service..."
            sudo systemctl stop zerotier-one 2>/dev/null || true
            sudo systemctl disable zerotier-one 2>/dev/null || true
            
            green_echo "[*] Removing ZeroTier package..."
            sudo apt remove --purge -y zerotier-one 2>/dev/null || true
            sudo apt autoremove -y
            
            green_echo "[*] Removing configuration..."
            sudo rm -rf /var/lib/zerotier-one
            
            green_echo "[+] ZeroTier has been uninstalled successfully!"
        fi
    fi
    
    # Uninstall NordVPN
    if command -v nordvpn &> /dev/null; then
        green_echo ""
        green_echo "[*] ========== Uninstalling NordVPN =========="
        
        # Try to use dedicated script if available, otherwise inline uninstall
        if [ -f "$SCRIPT_DIR/uninstall_nordvpn.sh" ]; then
            bash "$SCRIPT_DIR/uninstall_nordvpn.sh"
        else
            # Inline NordVPN uninstall logic
            green_echo "[*] Disconnecting and logging out..."
            nordvpn disconnect 2>/dev/null || true
            nordvpn logout 2>/dev/null || true
            nordvpn set meshnet off 2>/dev/null || true
            
            green_echo "[*] Removing NordVPN package..."
            sudo apt remove --purge -y nordvpn 2>/dev/null || true
            sudo apt autoremove -y
            
            green_echo "[*] Removing configuration..."
            rm -rf "$HOME/.config/nordvpn"
            sudo rm -rf /var/lib/nordvpn
            sudo rm -f /etc/systemd/system/nordvpnd.service
            
            green_echo "[*] Reloading systemd..."
            sudo systemctl daemon-reload
            
            green_echo "[+] NordVPN has been uninstalled successfully!"
        fi
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
