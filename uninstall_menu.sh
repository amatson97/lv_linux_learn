#!/bin/bash
# Uninstall Menu - Remove installed tools and configurations
# Description: Interactive menu to uninstall tools installed by lv_linux_learn

set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$script_dir/includes/main.sh"

UNINSTALL_SCRIPTS=(
  "uninstallers/uninstall_zerotier.sh"
  "uninstallers/uninstall_nordvpn.sh"
  "uninstallers/uninstall_docker.sh"
  "uninstallers/uninstall_chrome.sh"
  "uninstallers/uninstall_sublime.sh"
  "uninstallers/uninstall_flatpak.sh"
  "uninstallers/uninstall_wine.sh"
  "uninstallers/uninstall_nextcloud.sh"
  "scripts/remove_all_vpn.sh"
  "uninstallers/uninstall_all_vpn.sh"
  "uninstallers/clean_desktop_launchers.sh"
)

UNINSTALL_DESCRIPTIONS=(
  "Remove ZeroTier VPN, leave all networks, and clean configurations."
  "Remove NordVPN, logout from Meshnet, and clean configurations."
  "Remove Docker, all containers, images, volumes, and networks."
  "Remove Google Chrome web browser and optionally user data."
  "Remove Sublime Text editor and optionally user configuration."
  "Remove Flatpak and optionally all installed applications."
  "Remove Wine and optionally the Wine prefix data."
  "Remove Nextcloud Desktop client and optionally user configuration."
  "[Legacy] Remove all VPN clients (ZeroTier, NordVPN, Hamachi) - older script."
  "Remove all VPN tools (ZeroTier, NordVPN, Hamachi) in one operation."
  "Clean all desktop launchers and helper scripts from ~/.lv_connect."
)

# Display uninstall menu
show_uninstall_menu() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                   lv_linux_learn - Uninstaller Menu                            ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  for i in "${!UNINSTALL_SCRIPTS[@]}"; do
    local num=$((i + 1))
    local script="${UNINSTALL_SCRIPTS[$i]}"
    local desc="${UNINSTALL_DESCRIPTIONS[$i]}"
    
    # Check if script exists and is executable
    if [ ! -f "$script" ]; then
      printf "  \033[1;31m%2d)\033[0m \033[2m%-30s\033[0m \033[1;31m[MISSING]\033[0m\n" "$num" "$(basename "$script")"
    elif [ ! -x "$script" ]; then
      printf "  \033[1;33m%2d)\033[0m %-30s \033[1;33m[NOT EXECUTABLE]\033[0m\n" "$num" "$(basename "$script")"
    else
      printf "  \033[1;31m%2d)\033[0m %-30s\n" "$num" "$(basename "$script")"
    fi
    printf "      \033[2m%s\033[0m\n\n" "$desc"
  done
  
  echo "   0) Exit"
  echo
}

run_uninstall_script() {
  local script="$1"
  local script_name
  script_name="$(basename "$script")"
  
  if [ ! -f "$script" ]; then
    green_echo "[!] Error: Script not found: $script"
    return 1
  fi
  
  if [ ! -x "$script" ]; then
    green_echo "[!] Warning: Script is not executable. Making it executable..."
    chmod +x "$script" || {
      green_echo "[!] Error: Failed to make script executable. Running with bash..."
      bash "$script"
      return $?
    }
  fi
  
  green_echo "[*] Running $script_name..."
  echo "────────────────────────────────────────────────────────────────────────────────"
  
  if ./"$script"; then
    echo "────────────────────────────────────────────────────────────────────────────────"
    green_echo "[+] $script_name completed successfully"
  else
    local exit_code=$?
    echo "────────────────────────────────────────────────────────────────────────────────"
    green_echo "[!] $script_name exited with code $exit_code"
    return $exit_code
  fi
}

# Main loop
main() {
  while true; do
    show_uninstall_menu
    read -rp "Enter your choice [0-${#UNINSTALL_SCRIPTS[@]}]: " choice
    
    if [[ ! "$choice" =~ ^[0-9]+$ ]]; then
      green_echo "[!] Please enter a valid number."
      sleep 1
      continue
    fi
    
    if (( choice == 0 )); then
      green_echo "Exiting. Goodbye!"
      break
    elif (( choice >= 1 && choice <= ${#UNINSTALL_SCRIPTS[@]} )); then
      script="${UNINSTALL_SCRIPTS[$((choice-1))]}"
      run_uninstall_script "$script" || true
      echo
      green_echo "Press Enter to return to the menu..."
      read -r
    else
      green_echo "[!] Invalid choice: $choice (must be between 0 and ${#UNINSTALL_SCRIPTS[@]})"
      sleep 1
    fi
  done
}

main "$@"
