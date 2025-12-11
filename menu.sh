#!/bin/bash
# Interactive menu for lv_linux_learn scripts
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$script_dir/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$script_dir/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

SCRIPTS=(
  # Installation Scripts
  "scripts/new_vpn.sh"
  "scripts/chrome_install.sh"
  "scripts/docker_install.sh"
  "scripts/git_setup.sh"
  "scripts/install_flatpak.sh"
  "scripts/sublime_install.sh"
  "scripts/install_wine.sh"
  "scripts/nextcloud_client.sh"
  ""  # Separator
  # Utility Tools
  "tools/git_pull.sh"
  "tools/git_push_changes.sh"
  "tools/7z_extractor.sh"
  "tools/7z_extractor_ram_disk.sh"
  "tools/check_power_on_hours.sh"
  "tools/convert_7z_to_xiso.sh"
  "tools/extract_rar.sh"
  "tools/flac_to_mp3.sh"
  "tools/plex-batch-remux.sh"
  "tools/ubuntu_NetworkManager.sh"
  "tools/zip_extractor_ram_disk.sh"
  ""  # Separator
  # Bash Exercises
  "bash_exercises/hello_world.sh"
  "bash_exercises/show_date.sh"
  "bash_exercises/list_files.sh"
  "bash_exercises/make_directory.sh"
  "bash_exercises/print_numbers.sh"
  "bash_exercises/simple_calculator.sh"
  "bash_exercises/find_word.sh"
  "bash_exercises/count_lines.sh"
  ""  # Separator
  # Uninstall Options
  "uninstall_menu.sh"
)

DESCRIPTIONS=(
  # Installation Scripts
  "Installs ZeroTier VPN, joins Linux Learn Network, and removes conflicting VPNs."
  "Installs Google Chrome web browser for fast, secure internet browsing."
  "Installs Docker including engine, CLI, containerd, and plugins for container management."
  "Sets up Git and GitHub CLI with configuration and authentication for source control."
  "Installs Flatpak and Flathub repository for easy access to universal Linux apps."
  "Installs Sublime Text and Sublime Merge editors for code editing and version control."
  "Installs Wine/Winetricks and Microsoft Visual C++ 4.2 MFC runtime library (mfc42.dll)"
  "Install Nextcloud Desktop client, via flatpak."
  "── Utility Tools ──"
  # Utility Tools
  "Allows you to pull all changes down from the GitHub repository"
  "Allows you to add, commit and push all your changes to GitHub repository"
  "Extract all 7z archives in the current directory"
  "Extract 7z archives to a RAM disk for faster processing"
  "Check SMART power-on hours for drives in the system"
  "Convert 7z compressed Xbox ISO images to XISO format"
  "Extract all RAR archives in the current directory"
  "Convert FLAC audio files to MP3 format"
  "Batch remux video files for Plex compatibility"
  "Configure NetworkManager on Ubuntu"
  "Extract ZIP archives to a RAM disk"
  "── Bash Exercises ──"
  # Bash Exercises
  "Classic first program - prints 'Hello, World!'"
  "Displays current date and time"
  "Lists files in the current directory"
  "Creates a new directory with user input"
  "Prints numbers from 1 to 10 using a for loop"
  "Adds two numbers entered by user"
  "Searches for a word in a file using grep"
  "Counts lines in a file"
  "── System Management ──"
  # Uninstall Options
  "⚠️  Uninstall tools - Remove installed applications and clean configurations."
)

show_menu() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       lv_linux_learn - Script Menu                             ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  for i in "${!SCRIPTS[@]}"; do
    local num=$((i + 1))
    local script="${SCRIPTS[$i]}"
    local desc="${DESCRIPTIONS[$i]}"
    
    # Handle separator entries (empty script path)
    if [ -z "$script" ]; then
      printf "      \033[2m%s\033[0m\n\n" "$desc"
      continue
    fi
    
    # Check if script exists and is executable
    if [ ! -f "$script" ]; then
      printf "  \033[1;31m%2d)\033[0m \033[2m%-30s\033[0m \033[1;31m[MISSING]\033[0m\n" "$num" "$(basename "$script")"
    elif [ ! -x "$script" ]; then
      printf "  \033[1;33m%2d)\033[0m %-30s \033[1;33m[NOT EXECUTABLE]\033[0m\n" "$num" "$(basename "$script")"
    else
      printf "  \033[1;32m%2d)\033[0m %-30s\n" "$num" "$(basename "$script")"
    fi
    printf "      \033[2m%s\033[0m\n\n" "$desc"
  done
  
  echo "   0) Exit"
  echo
}

run_script() {
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

while true; do
  show_menu
  read -rp "Enter your choice [0-${#SCRIPTS[@]}]: " choice

  if [[ ! "$choice" =~ ^[0-9]+$ ]]; then
    green_echo "[!] Please enter a valid number."
    sleep 1
    continue
  fi

  if (( choice == 0 )); then
    green_echo "Exiting. Goodbye!"
    break
  elif (( choice >= 1 && choice <= ${#SCRIPTS[@]} )); then
    script="${SCRIPTS[$((choice-1))]}"
    
    # Skip separator entries
    if [ -z "$script" ]; then
      green_echo "[!] Invalid choice: separators cannot be executed"
      sleep 1
      continue
    fi
    
    run_script "$script" || true
    echo
    green_echo "Press Enter to return to the menu..."
    read -r
  else
    green_echo "[!] Invalid choice: $choice (must be between 0 and ${#SCRIPTS[@]})"
    sleep 1
  fi
done