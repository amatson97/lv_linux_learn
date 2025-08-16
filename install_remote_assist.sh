#!/bin/bash
# Installs NordVPN and sets up GNOME Remote Desktop + Meshnet info launcher.
# Run once. If user added to nordvpn group, you must reboot and re-run script to finish.
# The script will take the user through a guided install.
# An unistaller has been provided to easily remove this from your system. Disclaimers added to .md and this install.

# Includes
source includes/main.sh

set -e
NORDVPN_TOKEN="e9f2ab5ca361a4eddac74d6bb8b350d452f60bf0b81b4ca81ef3b6b8280644c0"
VNC_PORT="3389"
DESKTOP_LAUNCHER="$HOME/Desktop/ShowMeshnetInfo.desktop"

main() {
  source includes/main.sh
  green_echo "[*] Checking nordvpn group..."
  if ! getent group nordvpn > /dev/null; then
    green_echo "[*] Creating nordvpn group..."
    sudo groupadd nordvpn
  fi

  if ! user_in_nordvpn_group; then
    green_echo "[*] Adding user $USER to nordvpn group..."
    sudo usermod -aG nordvpn "$USER"
    green_echo
    green_echo "====================================================="
    green_echo "User $USER was added to 'nordvpn' group."
    green_echo "You must REBOOT your system now to apply this change."
    green_echo "After reboot, re-run this script to continue setup."
    green_echo "====================================================="
    exit 0
  fi

  green_echo "[*] User $USER is in 'nordvpn' group. Proceeding with installation..."

  green_echo "[*] Installing NordVPN..."
  sh <(wget -qO - https://downloads.nordcdn.com/apps/linux/install.sh) -p -y nordvpn-gui
  sudo apt install -y nordvpn
  nordvpn set notify off
  nordvpn set tray off

  green_echo "[*] Logging into NordVPN with token..."
  if [[ -z "$NORDVPN_TOKEN" ]]; then
    green_echo "[!] ERROR: NORDVPN_TOKEN is empty. Please set your token in the script."
    exit 1
  fi
  nordvpn login --token "$NORDVPN_TOKEN"

  green_echo "[*] Enabling NordVPN Meshnet..."
  nordvpn set meshnet on

  create_meshnet_info_desktop_icon
  nordvpn set autoconnect off
  green_echo "[✓] Setup complete! Use the desktop icon 'Show NordVPN Meshnet Info' on your desktop."
  green_echo "[!] DISCLAIMER: Your can remove this from your system running ./uninstall_remote_assist.sh"
  green_echo "    Remember to enable GNOME Remote Desktop (Settings → System → Remote Desktop)."
}

main