#!/bin/bash

# Description: Install Nextcloud Desktop Client for file synchronization

# Installs Nextcloud Desktop Client via Flatpak for seamless file synchronization
# with Nextcloud servers. Provides automatic sync, selective sync options,
# and integration with Ubuntu's file manager and system notifications.

set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Application identifiers (keep consistent with uninstaller)
APP_ID="com.nextcloud.desktopclient.nextcloud"
DESKTOP_DB_PATH="/var/lib/flatpak/exports/share/applications"

# Check if Nextcloud client already installed
if flatpak list 2>/dev/null | grep -q "$APP_ID"; then
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
flatpak install -y flathub "$APP_ID"

# ✅ Apply critical fix: Shared memory access for Qt QSharedMemory
green_echo "[*] Applying shared memory fix for Qt stability..."
sudo flatpak override --device=shm "$APP_ID"

# Refresh desktop integration
green_echo "[*] Updating desktop database..."
sudo update-desktop-database "$DESKTOP_DB_PATH"

green_echo "[+] Nextcloud Desktop Client installed successfully"
green_echo "    ✓ Flatpak shm override applied (fixes QSharedMemory crash)"
green_echo "    ✓ Desktop launcher ready"
green_echo "You may need to log out/in for full integration"

exit 0