#!/bin/bash
# Description: Install Flatpak universal package system with Flathub and Flatseal
#
# Sets up Flatpak universal package management system with GNOME Software
# integration. Adds Flathub repository for access to thousands of
# sandboxed applications with automatic updates and dependency management.
# Also installs Flatseal for managing Flatpak app permissions and portals.
#
set -euo pipefail

main() {
  local exit_code=0

  # Includes
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"

  # Create log directory if it doesn't exist
  mkdir -p "$HOME/.lv_linux_learn/logs"

  # Log file path
  LOG_FILE="$HOME/.lv_linux_learn/logs/flatpak_install_$(date +%Y%m%d_%H%M%S).log"

  # Redirect output to log file and terminal
  exec > >(tee -a "$LOG_FILE") 2>&1

  green_echo "[*] Installation logs saved to: $LOG_FILE"
  green_echo ""

  # Check for required tools (sudo is always needed)
  if ! command -v sudo &> /dev/null; then
    green_echo "[!] Error: This script requires sudo"
    exit_code=1
  fi

  # Detect package manager
  PACKAGE_MANAGER=""
  if command -v apt &> /dev/null; then
    PACKAGE_MANAGER="apt"
  elif command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
  elif command -v pacman &> /dev/null; then
    PACKAGE_MANAGER="pacman"
  else
    green_echo "[!] Unsupported package manager. This script supports apt, dnf, and pacman."
    exit_code=1
  fi

  if [ $exit_code -eq 0 ]; then
    green_echo "[*] Detected package manager: $PACKAGE_MANAGER"
    green_echo ""
  fi

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
    if confirm_action "Do you want to install the missing Flatpak components?" "Install Flatpak"; then
      # Update package list based on detected package manager
      case "$PACKAGE_MANAGER" in
        apt)
          sudo apt update -y || { green_echo "[!] Failed to update package list"; exit_code=1; }
          ;;
        dnf)
          sudo dnf check-update -y || { green_echo "[!] Failed to update package list"; exit_code=1; }
          ;;
        pacman)
          sudo pacman -Syu --noconfirm || { green_echo "[!] Failed to update package list"; exit_code=1; }
          ;;
      esac

      # Install packages based on detected package manager
      case "$PACKAGE_MANAGER" in
        apt)
          sudo apt install -y flatpak gnome-software-plugin-flatpak || { green_echo "[!] Failed to install packages"; exit_code=1; }
          ;;
        dnf)
          sudo dnf install -y flatpak gnome-software-plugin-flatpak || { green_echo "[!] Failed to install packages"; exit_code=1; }
          ;;
        pacman)
          sudo pacman -S --noconfirm flatpak gnome-software || { green_echo "[!] Failed to install packages"; exit_code=1; }
          ;;
      esac
    else
      green_echo "[!] Installation cancelled by user."
      exit_code=0
    fi
  fi

  # Add Flathub repository
  if [ $exit_code -eq 0 ]; then
    green_echo "[*] Adding flathub remote..."
    if ! flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo; then
      green_echo "[!] Failed to add Flathub repository"
      exit_code=1
    fi

    # Verify the remote was added
    if ! flatpak remotes | grep -q "flathub"; then
      green_echo "[!] Error: Flathub remote not found after adding"
      exit_code=1
    else
      green_echo "[+] Flathub remote configured successfully"
    fi
  fi

  # Install Flatseal for managing Flatpak permissions
  if [ $exit_code -eq 0 ]; then
    if flatpak list --app | grep -q "com.github.tchx84.Flatseal"; then
      green_echo "[+] Flatseal already installed"
    else
      green_echo "[*] Installing Flatseal (Flatpak permissions manager)..."
      if ! flatpak install -y flathub com.github.tchx84.Flatseal; then
        green_echo "[!] Failed to install Flatseal"
        exit_code=1
      fi
    fi
  fi

  # Final status message
  if [ $exit_code -eq 0 ]; then
    green_echo ""
    green_echo "[+] Flatpak setup complete successfully!"
    green_echo ""
    green_echo "📝 Notes:"
    green_echo "  • You may need to restart your session for full integration"
    green_echo "  • Use 'flatpak update' to check for app updates"
    green_echo "  • Manage permissions with Flatseal (installed above)"
    green_echo ""
    exit_code=0
  else
    green_echo "[!] Installation completed with errors. Check the log file for details."
    exit_code=1
  fi

  exit $exit_code
}

main "$@"
