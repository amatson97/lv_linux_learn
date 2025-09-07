#!/bin/bash

#functions
source includes/main.sh

set -e

# Update system
#green_echo "[*] Updating system..."
#sudo apt update && sudo apt upgrade -y

# Install Flatpak if not already installed
if ! command -v flatpak &> /dev/null; then
  green_echo "[*] Installing Flatpak..."
  sudo apt install flatpak -y
fi

# Add Flathub repository if not already added
if ! flatpak remote-list | grep -q flathub; then
  green_echo "[*] Adding Flathub repository..."
  sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

# Install Nextcloud desktop client via Flatpak
green_echo "[*] Installing Nextcloud Desktop Client via Flatpak..."
sudo flatpak install flathub com.nextcloud.desktopclient.nextcloud

green_echo "[*] Nextcloud Desktop Client installation complete."
green_echo "You may need to log out and back in or restart your system to update Flatpak environment."