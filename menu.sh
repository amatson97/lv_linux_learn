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

# Repository system
if [ -f "$script_dir/includes/repository.sh" ]; then
  # shellcheck source=/dev/null
  source "$script_dir/includes/repository.sh"
fi

# Custom scripts configuration
CUSTOM_SCRIPTS_DIR="$HOME/.lv_linux_learn"
CUSTOM_SCRIPTS_JSON="$CUSTOM_SCRIPTS_DIR/custom_scripts.json"

# Repository system variables
REPO_ENABLED=false
REPO_UPDATES_AVAILABLE=0

# Search filter
SEARCH_FILTER=""

SCRIPTS=(
  # Installation Scripts
  "scripts/new_vpn.sh"
  "scripts/chrome_install.sh"
  "scripts/docker_install.sh"
  "scripts/git_setup.sh"
  "scripts/install_flatpak.sh"
  "scripts/sublime_install.sh"
  "scripts/vscode_install.sh"
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
  "uninstallers/uninstall_zerotier.sh"
  "uninstallers/uninstall_chrome.sh"
  "uninstallers/uninstall_docker.sh"
  "uninstallers/uninstall_flatpak.sh"
  "uninstallers/uninstall_sublime.sh"
  "uninstallers/uninstall_vscode.sh"
  "uninstallers/uninstall_wine.sh"
  "uninstallers/uninstall_nextcloud.sh"
  "uninstallers/uninstall_nordvpn.sh"
  "uninstallers/uninstall_all_vpn.sh"
  "uninstallers/clean_desktop_launchers.sh"
)

DESCRIPTIONS=(
  # Installation Scripts
  "Installs ZeroTier VPN, joins Linux Learn Network, and removes conflicting VPNs."
  "Installs Google Chrome web browser for fast, secure internet browsing."
  "Installs Docker including engine, CLI, containerd, and plugins for container management."
  "Sets up Git and GitHub CLI with configuration and authentication for source control."
  "Installs Flatpak and Flathub repository for easy access to universal Linux apps."
  "Installs Sublime Text and Sublime Merge editors for code editing and version control."
  "Installs Visual Studio Code editor with IntelliSense, debugging, and extension support."
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
  "Classic first program with formatted output and educational explanations"
  "Displays date/time in 5+ formats (ISO 8601, Unix timestamp, 12-hour, etc.)"
  "Lists files with multiple ls options (basic, -lh, -lha) and hidden files"
  "Creates directory with input validation and existence checking"
  "Prints numbers 1-10 with loop examples (brace expansion, seq, C-style)"
  "Performs all basic math (+, -, ×, ÷) with input validation and error handling"
  "Searches files with grep, shows match count, lists available files first"
  "Counts lines/words/characters/bytes, demonstrates all wc command options"
  "── Uninstall ──"
  # Uninstall Options
  "Remove ZeroTier VPN (leaves networks first, removes service and configuration)"
  "Remove Google Chrome (optional: remove user data and configuration)"
  "⚠️  Remove Docker (warns about data loss, removes engine, CLI, and containers)"
  "Remove Flatpak (optional: remove installed apps and Flathub repository)"
  "Remove Sublime Text and Sublime Merge (optional: remove configuration)"
  "Remove Visual Studio Code (optional: remove extensions and configuration)"
  "Remove Wine and Winetricks (optional: remove Wine prefix and installed apps)"
  "Remove Nextcloud Desktop Client (optional: remove sync configuration)"
  "Remove NordVPN (disconnects, removes service, and group membership)"
  "⚠️  Remove ALL VPN tools at once (ZeroTier, NordVPN, Hamachi)"
  "Clean desktop launchers only (removes .lv_connect scripts and desktop icons)"
)

# Load custom scripts from JSON and append to arrays
load_custom_scripts() {
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    return 0
  fi
  
  # Check if jq is available
  if ! command -v jq &> /dev/null; then
    return 0
  fi
  
  # Simply append custom scripts at the end for now (simpler, always works)
  local custom_count
  custom_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON" 2>/dev/null || echo "0")
  
  if [ "$custom_count" -gt 0 ]; then
    # Add separator before custom scripts
    SCRIPTS+=("")
    DESCRIPTIONS+=("── Custom Scripts ──")
    
    # Add all custom scripts
    local i
    for ((i=0; i<custom_count; i++)); do
      local script_path name desc
      script_path=$(jq -r ".scripts[$i].script_path" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null)
      name=$(jq -r ".scripts[$i].name" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null)
      desc=$(jq -r ".scripts[$i].description" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null | sed 's/<[^>]*>//g')
      
      if [ -n "$script_path" ]; then
        SCRIPTS+=("$script_path")
        DESCRIPTIONS+=("📝 $desc")
      fi
    done
  fi
}

# Reload custom scripts (removes old custom scripts and reloads from JSON)
reload_custom_scripts() {
  # Remove all entries after index 41 (the last uninstaller)
  # This removes the separator and all custom scripts
  SCRIPTS=("${SCRIPTS[@]:0:42}")
  DESCRIPTIONS=("${DESCRIPTIONS[@]:0:42}")
  
  # Reload custom scripts
  load_custom_scripts
}

# Initialize: load custom scripts
load_custom_scripts

# Initialize repository system
if type -t init_repo_config &>/dev/null; then
  init_repo_config
  REPO_ENABLED=true
  # Check for updates on startup if auto-check is enabled
  if [ "$(get_config_value 'auto_check_updates' 'true')" = "true" ]; then
    check_for_updates &>/dev/null || true
  fi
fi

# Current menu state
CURRENT_CATEGORY=""

show_main_menu() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       LV Script Manager - Main Menu                            ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Count scripts in each category
  local install_count tools_count exercises_count uninstall_count custom_count
  install_count=9
  tools_count=11
  exercises_count=8
  uninstall_count=11
  custom_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON" 2>/dev/null || echo "0")
  
  echo "  Select a category:"
  echo
  printf "   \033[1;32m1)\033[0m 📦 Install Scripts         (%d scripts)\n" "$install_count"
  echo "      System tools, browsers, development environments"
  echo
  printf "   \033[1;32m2)\033[0m 🔧 Tools & Utilities       (%d scripts)\n" "$tools_count"
  echo "      File management, git helpers, conversion tools"
  echo
  printf "   \033[1;32m3)\033[0m 📚 Bash Exercises          (%d exercises)\n" "$exercises_count"
  echo "      Learn bash scripting with interactive examples"
  echo
  printf "   \033[1;32m4)\033[0m ⚠️  Uninstall               (%d scripts)\n" "$uninstall_count"
  echo "      Remove installed applications and clean configurations"
  echo
  if [ "$custom_count" -gt 0 ]; then
    printf "   \033[1;32m5)\033[0m 📝 Custom Scripts          (%d scripts)\n" "$custom_count"
    echo "      Your personally added scripts"
    echo
  fi
  
  # Show repository option if enabled
  if [ "$REPO_ENABLED" = true ]; then
    local repo_status="enabled"
    if [ "$REPO_UPDATES_AVAILABLE" -gt 0 ]; then
      repo_status="$REPO_UPDATES_AVAILABLE updates available"
    fi
    printf "   \033[1;32m6)\033[0m 📦 Script Repository       (%s)\n" "$repo_status"
    echo "      Download and update scripts from remote repository"
    echo
  fi
  
  echo "  ────────────────────────────────────────────────────────────────────────────"
  echo "   a) Add Custom Script    h) Help/About    s) Search All    u) Check Updates    0) Exit"
  echo
}

show_menu() {
  local category="$1"
  clear
  
  # Reset display-to-index mapping
  DISPLAY_TO_INDEX=()
  
  local title
  case "$category" in
    install) title="Install Scripts" ;;
    tools) title="Tools & Utilities" ;;
    exercises) title="Bash Exercises" ;;
    uninstall) title="Uninstall" ;;
    custom) title="Custom Scripts" ;;
    *) title="All Scripts" ;;
  esac
  
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  printf "║                       LV Script Manager - %-36s ║\n" "$title"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  
  if [ -n "$SEARCH_FILTER" ]; then
    echo "  🔍 Filter: \"$SEARCH_FILTER\" (press 's' to change/clear)"
  fi
  echo
  
  local display_count=0
  local start_idx=0 end_idx=0
  
  # Determine range based on category
  case "$category" in
    install)
      start_idx=0; end_idx=8
      ;;
    tools)
      start_idx=10; end_idx=20
      ;;
    exercises)
      start_idx=22; end_idx=29
      ;;
    uninstall)
      start_idx=31; end_idx=41
      ;;
    custom)
      # Show only custom scripts
      start_idx=43; end_idx=100
      ;;
  esac
  
  for i in "${!SCRIPTS[@]}"; do
    # Filter by category if specified
    if [ -n "$category" ] && [ "$category" != "custom" ]; then
      if [ "$i" -lt "$start_idx" ] || [ "$i" -gt "$end_idx" ]; then
        continue
      fi
    elif [ "$category" = "custom" ]; then
      # Only show custom scripts (after separator at index 42)
      if [ "$i" -le 42 ]; then
        continue
      fi
    fi
    
    local num=$((i + 1))
    local script="${SCRIPTS[$i]}"
    local desc="${DESCRIPTIONS[$i]}"
    
    # Handle separator entries (empty script path)
    if [ -z "$script" ]; then
      if [ -z "$SEARCH_FILTER" ]; then
        printf "\n  \033[1m%s\033[0m\n" "$desc"
      fi
      continue
    fi
    
    # Apply search filter
    if [ -n "$SEARCH_FILTER" ]; then
      local script_name
      script_name=$(basename "$script" 2>/dev/null || echo "")
      if ! echo "$script_name $desc" | grep -qi "$SEARCH_FILTER"; then
        continue
      fi
    fi
    
    display_count=$((display_count + 1))
    
    # Check if script exists and is executable
    local script_name
    script_name=$(basename "$script" 2>/dev/null || echo "unknown")
    
    # Use display_count for category views, original index for full list
    local show_num
    if [ -n "$category" ]; then
      show_num=$display_count
      # Map display number to actual array index
      DISPLAY_TO_INDEX[$show_num]=$i
    else
      show_num=$num
    fi
    
    # Compact format: number, name, status on one line
    if [ ! -f "$script" ]; then
      printf "  \033[1;31m%2d)\033[0m %-35s \033[1;31m[MISSING]\033[0m\n" "$show_num" "$script_name"
    elif [ ! -x "$script" ]; then
      printf "  \033[1;33m%2d)\033[0m %-35s \033[1;33m[NOT EXEC]\033[0m\n" "$show_num" "$script_name"
    else
      printf "  \033[1;32m%2d)\033[0m %-35s\n" "$show_num" "$script_name"
    fi
    # Description indented on next line
    printf "      \033[2m%s\033[0m\n" "$desc"
  done
  
  if [ -n "$SEARCH_FILTER" ] && [ "$display_count" -eq 0 ]; then
    echo "  No scripts match your search filter."
  fi
  
  echo
  echo "  ────────────────────────────────────────────────────────────────────────────"
  if [ -n "$category" ]; then
    if [ "$category" = "custom" ]; then
      echo "   e) Edit Script    d) Delete Script    b) Back    s) Search    0) Exit"
    else
      echo "   b) Back to Main Menu    s) Search    0) Exit"
    fi
  else
    echo "   a) Add Custom Script    h) Help/About    s) Search    0) Exit"
  fi
  echo
}

add_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Add Custom Script                                      ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  green_echo "Type 'cancel' or 'back' at any prompt to exit"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    green_echo "[*] Install it with: sudo apt install jq"
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Ensure config directory exists
  mkdir -p "$CUSTOM_SCRIPTS_DIR/scripts"
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    echo '{"scripts":[]}' > "$CUSTOM_SCRIPTS_JSON"
  fi
  
  # Get script name
  read -rp "Script Name: " script_name
  if [[ "$script_name" == "cancel" || "$script_name" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$script_name" ]; then
    green_echo "[!] Script name cannot be empty"
    sleep 2
    return 1
  fi
  
  # Get script path
  read -rp "Script Path (absolute): " script_path
  if [[ "$script_path" == "cancel" || "$script_path" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$script_path" ]; then
    green_echo "[!] Script path cannot be empty"
    sleep 2
    return 1
  fi
  
  # Validate script exists
  if [ ! -f "$script_path" ]; then
    green_echo "[!] Script file not found: $script_path"
    sleep 2
    return 1
  fi
  
  # Make executable if not already
  if [ ! -x "$script_path" ]; then
    green_echo "[*] Making script executable..."
    chmod +x "$script_path" || {
      green_echo "[!] Failed to make script executable"
      sleep 2
      return 1
    }
  fi
  
  # Get category
  echo
  echo "Select category:"
  echo "  1) Install"
  echo "  2) Tools"
  echo "  3) Exercises"
  echo "  4) Uninstall"
  read -rp "Choice [1-4]: " cat_choice
  
  if [[ "$cat_choice" == "cancel" || "$cat_choice" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  
  case "$cat_choice" in
    1) category="install" ;;
    2) category="tools" ;;
    3) category="exercises" ;;
    4) category="uninstall" ;;
    *)
      green_echo "[!] Invalid category"
      sleep 2
      return 1
      ;;
  esac
  
  # Get description
  echo
  green_echo "Enter description (one line, or press Enter to skip):"
  read -r description
  if [[ "$description" == "cancel" || "$description" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$description" ]; then
    description="Custom script"
  fi
  
  # Get sudo requirement
  read -rp "Requires sudo? [y/N]: " needs_sudo
  if [[ "$needs_sudo" == "cancel" || "$needs_sudo" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  requires_sudo="false"
  if [[ "$needs_sudo" =~ ^[Yy] ]]; then
    requires_sudo="true"
  fi
  
  # Generate UUID
  script_id=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)
  created_date=$(date -Iseconds)
  
  # Add to JSON
  local temp_json
  temp_json=$(mktemp)
  jq --arg id "$script_id" \
     --arg name "$script_name" \
     --arg category "$category" \
     --arg path "$script_path" \
     --arg desc "$description" \
     --argjson sudo "$requires_sudo" \
     --arg date "$created_date" \
     '.scripts += [{
       id: $id,
       name: $name,
       category: $category,
       script_path: $path,
       description: $desc,
       requires_sudo: $sudo,
       created_date: $date,
       is_custom: true
     }]' "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script added successfully!"
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
  sleep 1
}

edit_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Edit Custom Script                                     ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Check if custom scripts exist
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    green_echo "[!] No custom scripts found."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  local script_count
  script_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON")
  
  if [ "$script_count" -eq 0 ]; then
    green_echo "[!] No custom scripts to edit."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # List custom scripts
  green_echo "Custom Scripts:"
  echo
  jq -r '.scripts[] | "\(.name) - \(.category)"' "$CUSTOM_SCRIPTS_JSON" | nl -w2 -s') '
  echo
  
  read -rp "Enter script number to edit (or 'cancel'): " script_num
  
  if [[ "$script_num" == "cancel" || "$script_num" == "back" ]]; then
    return 0
  fi
  
  if ! [[ "$script_num" =~ ^[0-9]+$ ]] || [ "$script_num" -lt 1 ] || [ "$script_num" -gt "$script_count" ]; then
    green_echo "[!] Invalid script number"
    sleep 2
    return 1
  fi
  
  # Get script details (jq arrays are 0-indexed)
  local idx=$((script_num - 1))
  local script_id
  script_id=$(jq -r ".scripts[$idx].id" "$CUSTOM_SCRIPTS_JSON")
  
  green_echo "[*] Editing: $(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")"
  green_echo "Type 'cancel' or 'back' at any prompt to exit"
  green_echo "Press Enter to keep current value"
  echo
  
  # Get new values or keep existing
  local current_name current_category current_path current_desc current_sudo
  current_name=$(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")
  current_category=$(jq -r ".scripts[$idx].category" "$CUSTOM_SCRIPTS_JSON")
  current_path=$(jq -r ".scripts[$idx].script_path" "$CUSTOM_SCRIPTS_JSON")
  current_desc=$(jq -r ".scripts[$idx].description" "$CUSTOM_SCRIPTS_JSON")
  current_sudo=$(jq -r ".scripts[$idx].requires_sudo" "$CUSTOM_SCRIPTS_JSON")
  
  read -rp "Script Name [$current_name]: " new_name
  if [[ "$new_name" == "cancel" || "$new_name" == "back" ]]; then return 0; fi
  [ -z "$new_name" ] && new_name="$current_name"
  
  read -rp "Script Path [$current_path]: " new_path
  if [[ "$new_path" == "cancel" || "$new_path" == "back" ]]; then return 0; fi
  [ -z "$new_path" ] && new_path="$current_path"
  
  # Validate new path if changed
  if [ "$new_path" != "$current_path" ] && [ ! -f "$new_path" ]; then
    green_echo "[!] Warning: Script file not found: $new_path"
    read -rp "Continue anyway? [y/N]: " continue_edit
    if [[ ! "${continue_edit,,}" == "y" ]]; then
      return 1
    fi
  fi
  
  echo
  echo "Category: 1) install  2) tools  3) exercises  4) uninstall"
  read -rp "Category [$current_category]: " new_category_num
  if [[ "$new_category_num" == "cancel" || "$new_category_num" == "back" ]]; then return 0; fi
  
  local new_category="$current_category"
  if [ -n "$new_category_num" ]; then
    case "$new_category_num" in
      1) new_category="install" ;;
      2) new_category="tools" ;;
      3) new_category="exercises" ;;
      4) new_category="uninstall" ;;
      *) green_echo "[!] Invalid category, keeping current"; new_category="$current_category" ;;
    esac
  fi
  
  read -rp "Description [$current_desc]: " new_desc
  if [[ "$new_desc" == "cancel" || "$new_desc" == "back" ]]; then return 0; fi
  [ -z "$new_desc" ] && new_desc="$current_desc"
  
  read -rp "Requires sudo? [y/N] (current: $current_sudo): " new_sudo_input
  if [[ "$new_sudo_input" == "cancel" || "$new_sudo_input" == "back" ]]; then return 0; fi
  
  local new_sudo="$current_sudo"
  if [ -n "$new_sudo_input" ]; then
    if [[ "$new_sudo_input" =~ ^[Yy] ]]; then
      new_sudo="true"
    else
      new_sudo="false"
    fi
  fi
  
  # Update the script in JSON
  local temp_json
  temp_json=$(mktemp)
  jq --arg id "$script_id" \
     --arg name "$new_name" \
     --arg category "$new_category" \
     --arg path "$new_path" \
     --arg desc "$new_desc" \
     --argjson sudo "$new_sudo" \
     '(.scripts[] | select(.id == $id)) |= {
       id: $id,
       name: $name,
       category: $category,
       script_path: $path,
       description: $desc,
       requires_sudo: $sudo,
       created_date: .created_date,
       is_custom: true
     }' "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script updated successfully!"
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
  sleep 1
}

delete_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Delete Custom Script                                   ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Check if custom scripts exist
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    green_echo "[!] No custom scripts found."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  local script_count
  script_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON")
  
  if [ "$script_count" -eq 0 ]; then
    green_echo "[!] No custom scripts to delete."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # List custom scripts
  green_echo "Custom Scripts:"
  echo
  jq -r '.scripts[] | "\(.name) - \(.category) - \(.script_path)"' "$CUSTOM_SCRIPTS_JSON" | nl -w2 -s') '
  echo
  
  read -rp "Enter script number to delete (or 'cancel'): " script_num
  
  if [[ "$script_num" == "cancel" || "$script_num" == "back" ]]; then
    return 0
  fi
  
  if ! [[ "$script_num" =~ ^[0-9]+$ ]] || [ "$script_num" -lt 1 ] || [ "$script_num" -gt "$script_count" ]; then
    green_echo "[!] Invalid script number"
    sleep 2
    return 1
  fi
  
  # Get script details for confirmation
  local idx=$((script_num - 1))
  local script_name
  script_name=$(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")
  
  echo
  green_echo "[!] WARNING: This will permanently delete: $script_name"
  read -rp "Are you sure? [y/N]: " confirm
  
  if [[ ! "${confirm,,}" == "y" ]]; then
    green_echo "[*] Deletion cancelled"
    sleep 1
    return 0
  fi
  
  # Delete the script from JSON
  local temp_json
  temp_json=$(mktemp)
  jq "del(.scripts[$idx])" "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script deleted successfully!"
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
  sleep 1
}

show_repository_menu() {
  if [ "$REPO_ENABLED" != true ]; then
    green_echo "[!] Repository system not available"
    sleep 2
    return 1
  fi
  
  while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       Script Repository Manager                                ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo
    
    local total_scripts=$(jq -r '.scripts | length' "$MANIFEST_FILE" 2>/dev/null || echo "0")
    local cached_count=$(count_cached_scripts)
    local updates="$REPO_UPDATES_AVAILABLE"
    
    echo "  Repository Status:"
    echo "  • Available scripts: $total_scripts"
    echo "  • Cached locally:    $cached_count"
    echo "  • Updates available: $updates"
    echo
    echo "  Options:"
    printf "   \033[1;32m1)\033[0m Update All Scripts         ($updates updates)\n"
    echo "   2) Download All Scripts        (bulk download)"
    echo "   3) View Cached Scripts         (list local cache)"
    echo "   4) Clear Script Cache          (remove all cached)"
    echo "   5) Check for Updates           (manual refresh)"
    echo "   6) Repository Settings"
    echo
    echo "  ──────────────────────────────────────────────────────────────────────────────"
    echo "   b) Back to Main Menu    0) Exit"
    echo
    
    read -rp "Enter your choice: " repo_choice
    
    case "$repo_choice" in
      1)
        update_all_scripts
        read -rp "Press Enter to continue..."
        ;;
      2)
        green_echo "[*] This will download all $total_scripts scripts from the repository."
        read -rp "Continue? [y/N]: " confirm
        if [[ "${confirm,,}" == "y" ]]; then
          download_all_scripts
        fi
        read -rp "Press Enter to continue..."
        ;;
      3)
        clear
        list_cached_scripts
        read -rp "Press Enter to continue..."
        ;;
      4)
        clear_script_cache
        read -rp "Press Enter to continue..."
        ;;
      5)
        green_echo "[*] Checking for updates..."
        check_for_updates
        green_echo "[+] Update check complete. $REPO_UPDATES_AVAILABLE updates available."
        read -rp "Press Enter to continue..."
        ;;
      6)
        show_repo_settings
        ;;
      b|B)
        return 0
        ;;
      0)
        green_echo "Exiting. Goodbye!"
        exit 0
        ;;
      *)
        green_echo "[!] Invalid choice"
        sleep 1
        ;;
    esac
  done
}

show_repo_settings() {
  while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       Repository Settings                                      ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo
    
    local use_remote=$(get_config_value "use_remote_scripts" "true")
    local auto_check=$(get_config_value "auto_check_updates" "true")
    local auto_install=$(get_config_value "auto_install_updates" "true")
    local interval=$(get_config_value "update_check_interval_minutes" "30")
    
    echo "  Current Settings:"
    echo "  1) Use Remote Scripts:      $use_remote"
    echo "  2) Auto-check Updates:      $auto_check"
    echo "  3) Auto-install Updates:    $auto_install"
    echo "  4) Check Interval:          $interval minutes"
    echo
    echo "  Options:"
    echo "  r) Toggle remote scripts"
    echo "  c) Toggle auto-check"
    echo "  i) Toggle auto-install"
    echo "  t) Change interval"
    echo "  d) Reset to defaults"
    echo "  b) Back"
    echo
    
    read -rp "Enter your choice: " settings_choice
    
    case "$settings_choice" in
      r|R)
        if [ "$use_remote" = "true" ]; then
          set_config_value "use_remote_scripts" "false"
          green_echo "[*] Remote scripts disabled"
        else
          set_config_value "use_remote_scripts" "true"
          green_echo "[*] Remote scripts enabled"
        fi
        sleep 1
        ;;
      c|C)
        if [ "$auto_check" = "true" ]; then
          set_config_value "auto_check_updates" "false"
          green_echo "[*] Auto-check disabled"
        else
          set_config_value "auto_check_updates" "true"
          green_echo "[*] Auto-check enabled"
        fi
        sleep 1
        ;;
      i|I)
        if [ "$auto_install" = "true" ]; then
          set_config_value "auto_install_updates" "false"
          green_echo "[*] Auto-install disabled"
        else
          set_config_value "auto_install_updates" "true"
          green_echo "[*] Auto-install enabled"
        fi
        sleep 1
        ;;
      t|T)
        read -rp "Enter interval in minutes [30]: " new_interval
        if [[ "$new_interval" =~ ^[0-9]+$ ]]; then
          set_config_value "update_check_interval_minutes" "$new_interval"
          green_echo "[*] Interval updated to $new_interval minutes"
        else
          green_echo "[!] Invalid number"
        fi
        sleep 1
        ;;
      d|D)
        green_echo "[*] Resetting to defaults..."
        init_repo_config
        green_echo "[+] Settings reset"
        sleep 1
        ;;
      b|B)
        return 0
        ;;
      *)
        green_echo "[!] Invalid choice"
        sleep 1
        ;;
    esac
  done
}

show_help() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       LV Script Manager - Help                                 ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  green_echo "ABOUT"
  echo "  LV Script Manager - A curated collection of Ubuntu setup scripts and utilities"
  echo "  Repository: https://github.com/amatson97/lv_linux_learn"
  echo "  License: MIT"
  echo
  green_echo "USAGE"
  echo "  • Select a script number to run it"
  echo "  • Press 'a' to add your own custom scripts"
  echo "  • Press 's' to search/filter scripts"
  echo "  • Press 'h' to see this help screen"
  echo "  • Press '0' to exit"
  echo
  green_echo "CUSTOM SCRIPTS"
  echo "  • Add your own scripts without editing code"
  echo "  • Scripts are stored in: ~/.lv_linux_learn/"
  echo "  • Custom scripts marked with 📝 emoji"
  echo "  • Requires 'jq' package: sudo apt install jq"
  echo
  green_echo "TABS/CATEGORIES"
  echo "  • Install: System tools and applications"
  echo "  • Tools: Utility scripts for file management and tasks"
  echo "  • Exercises: Bash learning exercises"
  echo "  • Uninstall: Safely remove installed tools"
  echo
  green_echo "DOCUMENTATION"
  echo "  • Quick Start: $script_dir/README.md"
  echo "  • Custom Scripts: $script_dir/docs/CUSTOM_SCRIPTS.md"
  echo "  • Examples: $script_dir/examples/"
  echo
  green_echo "SUPPORT"
  echo "  • GitHub Issues: https://github.com/amatson97/lv_linux_learn/issues"
  echo "  • Target Environment: Ubuntu 24.04.3 LTS Desktop"
  echo
  read -rp "Press Enter to return to menu..."
}

search_scripts() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Search/Filter Scripts                                  ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  if [ -n "$SEARCH_FILTER" ]; then
    echo "  Current filter: \"$SEARCH_FILTER\""
    echo
  fi
  
  read -rp "Enter search term (or leave empty to clear): " new_filter
  SEARCH_FILTER="$new_filter"
  
  if [ -n "$SEARCH_FILTER" ]; then
    green_echo "[*] Filter applied: \"$SEARCH_FILTER\""
  else
    green_echo "[*] Filter cleared"
  fi
  sleep 1
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
  
  # Run script - check if absolute or relative path
  local exit_code=0
  if [[ "$script" = /* ]]; then
    # Absolute path - run directly
    "$script" || exit_code=$?
  else
    # Relative path - run with ./
    ./"$script" || exit_code=$?
  fi
  
  echo "────────────────────────────────────────────────────────────────────────────────"
  if [ $exit_code -eq 0 ]; then
    green_echo "[+] $script_name completed successfully"
  else
    green_echo "[!] $script_name exited with code $exit_code"
    return $exit_code
  fi
}

while true; do
  # Show appropriate menu
  if [ -z "$CURRENT_CATEGORY" ]; then
    show_main_menu
  else
    show_menu "$CURRENT_CATEGORY"
  fi
  
  read -rp "Enter your choice: " choice

  # Handle letter commands
  case "$choice" in
    0)
      green_echo "Exiting. Goodbye!"
      break
      ;;
    a|A)
      if [ -z "$CURRENT_CATEGORY" ]; then
        add_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
    b|B)
      # Back to main menu
      CURRENT_CATEGORY=""
      SEARCH_FILTER=""
      continue
      ;;
    h|H)
      if [ -z "$CURRENT_CATEGORY" ]; then
        show_help
      else
        green_echo "[!] Invalid choice in this menu. Press 'b' for main menu."
        sleep 1
      fi
      continue
      ;;
    u|U)
      if [ -z "$CURRENT_CATEGORY" ] && [ "$REPO_ENABLED" = true ]; then
        green_echo "[*] Checking for updates..."
        check_for_updates
        green_echo "[+] Update check complete. $REPO_UPDATES_AVAILABLE updates available."
        sleep 2
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
    s|S)
      search_scripts
      continue
      ;;
    e|E)
      if [ "$CURRENT_CATEGORY" = "custom" ]; then
        edit_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
    d|D)
      if [ "$CURRENT_CATEGORY" = "custom" ]; then
        delete_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
  esac

  # Handle numeric choices for main menu categories
  if [ -z "$CURRENT_CATEGORY" ]; then
    case "$choice" in
      1)
        CURRENT_CATEGORY="install"
        continue
        ;;
      2)
        CURRENT_CATEGORY="tools"
        continue
        ;;
      3)
        CURRENT_CATEGORY="exercises"
        continue
        ;;
      4)
        CURRENT_CATEGORY="uninstall"
        continue
        ;;
      5)
        CURRENT_CATEGORY="custom"
        continue
        ;;
      6)
        if [ "$REPO_ENABLED" = true ]; then
          show_repository_menu
        else
          green_echo "[!] Invalid choice"
          sleep 1
        fi
        continue
        ;;
      *)
        green_echo "[!] Invalid choice. Select 1-5, or: a (add), h (help), s (search), 0 (exit)"
        sleep 2
        continue
        ;;
    esac
  fi

  # Handle numeric choices for script execution
  if [[ ! "$choice" =~ ^[0-9]+$ ]]; then
    green_echo "[!] Invalid choice. Use a number, s (search), b (back), or 0 (exit)"
    sleep 2
    continue
  fi

  # Map display number to actual index if in a category view
  actual_index=""
  if [ -n "$CURRENT_CATEGORY" ] && [ -n "${DISPLAY_TO_INDEX[$choice]}" ]; then
    actual_index=${DISPLAY_TO_INDEX[$choice]}
  else
    actual_index=$((choice-1))
  fi

  if [ -n "${SCRIPTS[$actual_index]}" ]; then
    script="${SCRIPTS[$actual_index]}"
    
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
    green_echo "[!] Invalid choice: $choice (must be between 1 and ${#SCRIPTS[@]})"
    sleep 2
  fi
done