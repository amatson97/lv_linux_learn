#!/bin/bash
# Install Nextcloud Desktop Client via Flatpak
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

# Check if Nextcloud client already installed
if flatpak list 2>/dev/null | grep -q com.nextcloud.desktopclient.nextcloud; then
  green_echo "[+] Nextcloud Desktop Client already installed"
  exit 0
fi

# Install Flatpak if not already installed
if ! command -v flatpak &> /dev/null; then
  green_echo "[*] Installing Flatpak..."
  sudo apt update -y
  sudo apt install -y flatpak
fi

# Add Flathub repository if not already added
if ! flatpak remote-list | grep -q flathub; then
  green_echo "[*] Adding Flathub repository..."
  flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

# Install Nextcloud desktop client via Flatpak
green_echo "[*] Installing Nextcloud Desktop Client..."
flatpak install -y flathub com.nextcloud.desktopclient.nextcloud

green_echo "[+] Nextcloud Desktop Client installed successfully"
green_echo "You may need to log out and back in for full desktop integration"