#!/bin/bash
# Install ZeroTier VPN and join Linux Learn Network
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# https://my.zerotier.com/network/8bd5124fd60a971f
# Installs zerotier and joins the Linux Learn Network.
# Removes conflicting VPNs (NordVPN, LogMeIn Hamachi) if present.

#nettowrk ID
ZEROTIER_NETWORK=8bd5124fd60a971f

#functions

#calling functions
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"
sleep 5
install_zerotier
set_permissions_zerotier_cli
create_zerotier_info_desktop_icon

green_echo "[+] Setup complete"
exit 0