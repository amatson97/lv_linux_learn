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

# Get ZeroTier Network ID interactively
green_echo "[*] ZeroTier Network Configuration"
green_echo "[*] You can find your network ID at: https://my.zerotier.com/"
echo ""

# Use environment variable if set, otherwise prompt user
if [ -n "${ZEROTIER_NETWORK_ID:-}" ]; then
  ZEROTIER_NETWORK="$ZEROTIER_NETWORK_ID"
  green_echo "[*] Using network ID from environment variable"
else
  ZEROTIER_NETWORK=$(prompt_zerotier_network)
fi

readonly ZEROTIER_NETWORK

# Main execution
main() {
    green_echo "[*] Starting ZeroTier VPN installation and configuration..."
    
    # Remove conflicting VPN clients
    green_echo "[*] Checking for conflicting VPN installations..."
    remove_if_installed_nord "nordvpn"
    remove_if_installed_hamachi "logmein-hamachi"
    
    # Brief pause to ensure clean removal
    sleep 3
    
    # Install ZeroTier
    green_echo "[*] Installing ZeroTier..."
    sudo apt install curl -y
    curl -s https://install.zerotier.com | sudo bash
    
    # Wait for services to start up
    green_echo "[*] Waiting for ZeroTier service to initialize..."
    sleep 5
    
    # Join the network directly
    green_echo "[*] Joining ZeroTier network: $ZEROTIER_NETWORK"
    sudo zerotier-cli join "$ZEROTIER_NETWORK"
    
    green_echo "[✔] Successfully joined network: $ZEROTIER_NETWORK"
    
    green_echo "[*] Setting permissions for ZeroTier CLI..."
    set_permissions_zerotier_cli
    
    green_echo "[*] Creating desktop icon..."
    create_zerotier_info_desktop_icon
    
    green_echo "[+] Setup complete! ZeroTier VPN is now installed and configured."
    green_echo "[+] Network ID: ${ZEROTIER_NETWORK}"
}

# Run main function
main "$@"