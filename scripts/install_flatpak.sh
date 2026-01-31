#!/bin/bash
# Description: Install Flatpak universal package system with Flathub and Flatseal
#
# Sets up Flatpak universal package management system with GNOME Software
# integration. Adds Flathub repository for access to thousands of
# sandboxed applications with automatic updates and dependency management.
# Also installs Flatseal for managing Flatpak app permissions and portals.
#
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Check what needs to be installed
flatpak_installed=false
plugin_installed=false

if command -v flatpak &> /dev/null; then
  flatpak_installed=true
  green_echo "[+] Flatpak already installed ($(flatpak --version | tr -d '\n'))"
fi

if dpkg -l | grep -q "^ii.*gnome-software-plugin-flatpak"; then
  plugin_installed=true
  green_echo "[+] GNOME Software Flatpak plugin already installed"
fi

# Install missing components
if [ "$flatpak_installed" = false ] || [ "$plugin_installed" = false ]; then
  green_echo "[*] Installing missing Flatpak components..."
  sudo apt update -y
  sudo apt install -y flatpak gnome-software-plugin-flatpak
fi

# Add Flathub repository
green_echo "[*] Adding flathub remote..."
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Check if Flathub is configured
if flatpak remotes | grep -q flathub; then
  green_echo "[+] Flathub remote configured"
fi

# Install Flatseal for managing Flatpak permissions
if flatpak list --app | grep -q "com.github.tchx84.Flatseal"; then
  green_echo "[+] Flatseal already installed"
else
  green_echo "[*] Installing Flatseal (Flatpak permissions manager)..."
  flatpak install -y flathub com.github.tchx84.Flatseal
fi

green_echo "[+] Flatpak setup complete. You may need to restart your session for full integration."
exit 0
