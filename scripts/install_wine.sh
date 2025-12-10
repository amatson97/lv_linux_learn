#!/bin/bash
# Install Wine and Winetricks for running Windows apps on Ubuntu
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

# Check if Wine already installed
if command -v wine &> /dev/null; then
  green_echo "[+] Wine already installed ($(wine --version 2>/dev/null | tr -d '\n' || echo 'unknown version'))"
else
  # Enable 32-bit architecture for Wine
  green_echo "[*] Enabling 32-bit packages..."
  sudo dpkg --add-architecture i386
  
  # Update package lists
  sudo apt update -y
  
  # Install Wine and Winetricks
  green_echo "[*] Installing Wine and Winetricks..."
  sudo apt install -y wine winetricks
  
  green_echo "[+] Wine installed successfully"
fi

# Check if winetricks is available
if ! command -v winetricks &> /dev/null; then
  green_echo "[!] Winetricks not found, skipping mfc42 install"
  exit 1
fi

# Install Microsoft Visual C++ 4.2 MFC runtime library (mfc42.dll)
green_echo "[*] Installing MS Visual C++ 4.2 MFC Library (mfc42.dll)..."
if winetricks -q mfc42 2>/dev/null; then
  green_echo "[+] mfc42.dll installed successfully"
else
  green_echo "[!] Failed to install mfc42.dll (may already be installed or require user interaction)"
fi

green_echo "[+] Wine setup complete"

