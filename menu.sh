#!/bin/bash

# Includes
source includes/main.sh

SCRIPTS=(
  "scripts/new_vpn.sh"
  "scripts/remove_all_vpn.sh"
  "scripts/chrome_install.sh"
  "scripts/docker_install.sh"
  "scripts/git_setup.sh"
  "scripts/install_flatpak.sh"
  "scripts/sublime_install.sh"
  "scripts/git_setup.sh"
  "scripts/git_pull.sh"
  "scripts/git_push_changes.sh"
)

DESCRIPTIONS=(
  "Installs ZeroTier VPN, joins Linux Learn Network, and removes conflicting VPNs."
  "Removes all installed VPN clients including Zerotier, NordVPN, and LogMeIn Hamachi."
  "Installs Google Chrome web browser for fast, secure internet browsing."
  "Installs Docker including engine, CLI, containerd, and plugins for container management."
  "Sets up Git and GitHub CLI with configuration and authentication for source control."
  "Installs Flatpak and Flathub repository for easy access to universal Linux apps."
  "Installs Sublime Text and Sublime Merge editors for code editing and version control."
  "Guides you through setting up git in terminal."
  "Allows you to pull all chnages down from the GitHub repository"
  "Allows you to add, commit and push all your chnages to GitHub repository"
)

show_menu() {
  echo
  printf "%-4s %-20s  %s\n" "No." "Script Name" "Description"
  printf "%-4s %-20s  %s\n" "---" "-----------" "-----------"
  for i in "${!SCRIPTS[@]}"; do
    script_name=$(basename "${SCRIPTS[$i]}")
    printf "[%-4s %-20s  %s\n" "$((i+1))]" "$script_name" "${DESCRIPTIONS[$i]}"
  done
  echo "[0]   Exit"
  echo
}

while true; do
  show_menu
  read -rp "Enter your choice [0-${#SCRIPTS[@]}]: " choice

  if [[ "$choice" =~ ^[0-9]+$ ]]; then
    if (( choice == 0 )); then
      green_echo "Exiting."
      break
    elif (( choice >= 1 && choice <= ${#SCRIPTS[@]} )); then
      script="${SCRIPTS[$((choice-1))]}"
      green_echo "Running $script..."
      if [[ -x "$script" ]]; then
        ./"$script"
      else
        bash "$script"
      fi
      echo
      green_echo "Press Enter to return to the menu..."
      read -r
    else
      green_echo "Invalid choice: $choice"
    fi
  else
    green_echo "Please enter a valid number."
  fi
done