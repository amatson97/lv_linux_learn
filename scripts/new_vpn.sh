#!/bin/bash
# Install ZeroTier VPN and join configured network
# Description: Installs ZeroTier and joins a user-configured network.
#              Removes conflicting VPNs (NordVPN, LogMeIn Hamachi) if present.
#              Network ID must be provided via ZEROTIER_NETWORK_ID environment variable.

set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Constants
# Set your ZeroTier Network ID here or via ZEROTIER_NETWORK_ID environment variable
# Get your network ID from: https://my.zerotier.com/
readonly ZEROTIER_NETWORK="${ZEROTIER_NETWORK_ID:-REPLACE_WITH_YOUR_NETWORK_ID}"

# Validate network ID is configured
if [ "$ZEROTIER_NETWORK" = "REPLACE_WITH_YOUR_NETWORK_ID" ]; then
  green_echo "[!] Error: ZeroTier network ID not configured"
  green_echo "[*] Set ZEROTIER_NETWORK_ID environment variable or edit this script (line 18)"
  green_echo "[*] Get your network ID from: https://my.zerotier.com/"
  exit 1
fi

# Main execution
main() {
    green_echo "[*] Starting ZeroTier VPN installation and configuration..."
    
    # Remove conflicting VPN clients
    green_echo "[*] Checking for conflicting VPN installations..."
    remove_if_installed_nord "nordvpn"
    remove_if_installed_hamachi "logmein-hamachi"
    
    # Brief pause to ensure clean removal
    sleep 3
    
    # Install and configure ZeroTier
    green_echo "[*] Installing ZeroTier..."
    install_zerotier
    
    green_echo "[*] Setting permissions for ZeroTier CLI..."
    set_permissions_zerotier_cli
    
    green_echo "[*] Creating desktop icon..."
    create_zerotier_info_desktop_icon
    
    green_echo "[+] Setup complete! ZeroTier VPN is now installed and configured."
    green_echo "[+] Network ID: ${ZEROTIER_NETWORK}"
}

# Run main function
main "$@"