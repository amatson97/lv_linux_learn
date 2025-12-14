#!/bin/bash
# Description: Install Flatpak universal package system with Flathub repository
#
# Sets up Flatpak universal package management system with GNOME Software
# integration. Adds Flathub repository for access to thousands of
# sandboxed applications with automatic updates and dependency management.
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Check if already installed
if command -v flatpak &> /dev/null; then
  green_echo "[+] Flatpak already installed ($(flatpak --version | tr -d '\n'))"
  if flatpak remotes | grep -q flathub; then
    green_echo "[+] Flathub remote already configured"
    exit 0
  fi
else
  green_echo "[*] Installing flatpak..."
  sudo apt update -y
  sudo apt install -y flatpak gnome-software-plugin-flatpak
fi

green_echo "[*] Adding flathub remote..."
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

green_echo "[+] Flatpak setup complete. You may need to restart your session for full integration."
exit 0
