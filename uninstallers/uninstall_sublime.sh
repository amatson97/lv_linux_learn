#!/bin/bash
# Description: Remove Sublime Text and Sublime Merge with settings cleanup
#
# Uninstalls Sublime Text editor and Sublime Merge git client with
# complete removal of repositories, configuration files, and user settings.
# Provides option to backup settings before removal.
set -euo pipefail

# Includes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES_DIR="$SCRIPT_DIR/../includes"
if [ -f "$INCLUDES_DIR/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$INCLUDES_DIR/main.sh"
elif [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$HOME/lv_linux_learn/includes/main.sh"
else
    echo "Error: Could not find includes/main.sh"
    exit 1
fi

# Function to check and remove a package
remove_package() {
  local package="$1"
  local removed=0
  
  # Check apt/dpkg
  if dpkg -l "$package" 2>/dev/null | grep -q "^ii"; then
    green_echo "[*] Removing $package via apt..."
    sudo apt remove --purge -y "$package"
    sudo apt autoremove -y
    removed=1
  fi
  
  # Check snap
  if snap list "$package" &>/dev/null; then
    green_echo "[*] Removing $package via snap..."
    sudo snap remove "$package"
    removed=1
  fi
  
  # Check flatpak (try multiple potential names)
  if command -v flatpak &>/dev/null; then
    for flatpak_name in "$package" "com.sublimetext.${package^}" "com.sublimemerge.submerge"; do
      if flatpak list | grep -qi "$flatpak_name"; then
        green_echo "[*] Removing $flatpak_name via flatpak..."
        flatpak uninstall -y "$flatpak_name" || true
        removed=1
      fi
    done
  fi
  
  return $removed
}

green_echo "[*] Uninstalling Sublime Text..."

# Check if Sublime Text or Sublime Merge is installed
sublime_text_installed=0
sublime_merge_installed=0

# Quick check for Sublime Text
if command -v subl &>/dev/null || dpkg -l sublime-text 2>/dev/null | grep -q "^ii"; then
  sublime_text_installed=1
fi

# Quick check for Sublime Merge
if command -v smerge &>/dev/null || dpkg -l sublime-merge 2>/dev/null | grep -q "^ii"; then
  sublime_merge_installed=1
fi

# Exit early if nothing is installed
if [ "$sublime_text_installed" -eq 0 ] && [ "$sublime_merge_installed" -eq 0 ]; then
  green_echo "[!] Neither Sublime Text nor Sublime Merge is installed."
  green_echo "[*] Nothing to uninstall."
  exit 0
fi

# Check if Sublime Text is installed
if [ "$sublime_text_installed" -eq 1 ]; then
  remove_package "sublime-text"
  
  # Remove repository
  if [ -f /etc/apt/sources.list.d/sublime-text.list ]; then
    green_echo "[*] Removing Sublime Text repository..."
    sudo rm -f /etc/apt/sources.list.d/sublime-text.list
  fi
  
  # Remove GPG key
  if [ -f /usr/share/keyrings/sublimehq-archive.gpg ]; then
    green_echo "[*] Removing Sublime Text GPG key..."
    sudo rm -f /usr/share/keyrings/sublimehq-archive.gpg
  fi
  
  # Remove any remaining binaries
  if command -v subl &>/dev/null; then
    subl_path=$(which subl)
    green_echo "[!] Binary still exists at: $subl_path"
    read -rp "Remove binary manually? [y/N]: " remove_bin
    if [[ "${remove_bin,,}" == "y" ]]; then
      sudo rm -f "$subl_path"
    fi
  fi
  
  # Remove user config (optional - ask user)
  if [ -d "$HOME/.config/sublime-text" ]; then
    read -rp "Remove Sublime Text configuration files? [y/N]: " remove_config
    if [[ "${remove_config,,}" == "y" ]]; then
      green_echo "[*] Removing Sublime Text configuration..."
      rm -rf "$HOME/.config/sublime-text"
    fi
  fi
  
  green_echo "[+] Sublime Text uninstalled"
else
  green_echo "[!] Sublime Text is not installed."
fi

green_echo "[*] Uninstalling Sublime Merge..."

# Skip if not installed (already checked at the start)
if [ "$sublime_merge_installed" -eq 0 ]; then
  green_echo "[!] Sublime Merge is not installed."
else
  # Enhanced detection - check all possible locations
  merge_found=0

  # Check for smerge binary
  if command -v smerge &>/dev/null; then
    green_echo "[*] Found smerge binary at: $(which smerge)"
    merge_found=1
  fi

  # Check dpkg
  if dpkg -l sublime-merge 2>/dev/null | grep -q "^ii"; then
    green_echo "[*] Found sublime-merge package (apt/dpkg)"
    merge_found=1
  fi

  # Check snap
  if snap list sublime-merge &>/dev/null; then
    green_echo "[*] Found sublime-merge snap package"
    merge_found=1
  fi

  # Check flatpak with exact ID
  if command -v flatpak &>/dev/null; then
    if flatpak list --app | grep -qi "sublime"; then
      green_echo "[*] Found Sublime Merge in flatpak:"
      flatpak list --app | grep -i "sublime"
      merge_found=1
    fi
  fi

  # Check common installation directories
  for dir in /opt/sublime_merge /usr/share/sublime_merge /usr/local/sublime_merge "$HOME/.local/share/sublime_merge"; do
    if [ -d "$dir" ]; then
      green_echo "[*] Found Sublime Merge directory: $dir"
      merge_found=1
    fi
  done

  # Check desktop files
  for desktop_file in /usr/share/applications/sublime_merge.desktop "$HOME/.local/share/applications/sublime_merge.desktop"; do
    if [ -f "$desktop_file" ]; then
      green_echo "[*] Found desktop file: $desktop_file"
      merge_found=1
    fi
  done

  if [ "$merge_found" -eq 1 ]; then
    echo
    green_echo "[*] Attempting removal..."
    
    # Try standard package removal
    remove_package "sublime-merge"
    
    # Check for alternative package names in dpkg
    if dpkg -l 2>/dev/null | grep -qi "sublime.*merge"; then
      green_echo "[*] Found alternative Sublime Merge package..."
      dpkg -l | grep -i "sublime.*merge" | awk '{print $2}' | while read -r pkg; do
        green_echo "[*] Removing package: $pkg"
        sudo apt remove --purge -y "$pkg"
      done
      sudo apt autoremove -y
    fi
  
  # Remove flatpak with exact match
  if command -v flatpak &>/dev/null; then
    flatpak list --app | grep -i "sublime" | awk '{print $2}' | while read -r app_id; do
      green_echo "[*] Removing flatpak: $app_id"
      flatpak uninstall -y "$app_id" || true
    done
  fi
  
  # Remove remaining binaries
  if command -v smerge &>/dev/null; then
    smerge_path=$(which smerge)
    green_echo "[!] Binary still exists at: $smerge_path"
    read -rp "Remove binary manually? [y/N]: " remove_bin
    if [[ "${remove_bin,,}" == "y" ]]; then
      sudo rm -f "$smerge_path"
    fi
  fi
  
  # Remove installation directories
  for dir in /opt/sublime_merge /usr/share/sublime_merge /usr/local/sublime_merge; do
    if [ -d "$dir" ]; then
      green_echo "[!] Found installation directory: $dir"
      read -rp "Remove directory $dir? [y/N]: " remove_dir
      if [[ "${remove_dir,,}" == "y" ]]; then
        sudo rm -rf "$dir"
      fi
    fi
  done
  
  # Remove desktop files
  for desktop_file in /usr/share/applications/sublime_merge.desktop "$HOME/.local/share/applications/sublime_merge.desktop"; do
    if [ -f "$desktop_file" ]; then
      green_echo "[*] Removing desktop file: $desktop_file"
      rm -f "$desktop_file" 2>/dev/null || sudo rm -f "$desktop_file"
    fi
  done
  
  # Remove user config (optional - ask user)
  if [ -d "$HOME/.config/sublime-merge" ]; then
    read -rp "Remove Sublime Merge configuration files? [y/N]: " remove_config
    if [[ "${remove_config,,}" == "y" ]]; then
      green_echo "[*] Removing Sublime Merge configuration..."
      rm -rf "$HOME/.config/sublime-merge"
    fi
  fi
  
  # Remove local user installation
  if [ -d "$HOME/.local/share/sublime_merge" ]; then
    read -rp "Remove local Sublime Merge installation? [y/N]: " remove_local
    if [[ "${remove_local,,}" == "y" ]]; then
      rm -rf "$HOME/.local/share/sublime_merge"
    fi
  fi
  
  green_echo "[+] Sublime Merge removal complete"
  fi
fi

# Update package list
green_echo "[*] Updating package lists..."
sudo apt update -y

green_echo "[+] Sublime uninstall complete"
