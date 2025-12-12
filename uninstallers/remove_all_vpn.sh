#!/bin/bash
# Remove all VPN clients (ZeroTier, NordVPN, Hamachi)
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

#functions
remove_if_installed_zerotier "zerotier-one"
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"
remove_files

green_echo "[+] All VPN clients removed"
exit 0