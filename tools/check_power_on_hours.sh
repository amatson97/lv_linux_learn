#!/bin/bash
# Description: Check drive health and power-on hours using smartctl
#
# Analyzes storage device health by checking power-on hours, temperature,
# and SMART attributes for selected drives. Useful for monitoring drive
# wear and predicting potential failures in servers and workstations.
set -euo pipefail

# Parse command-line arguments
DEBUG=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug|-d)
      DEBUG=1
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--debug|-d] [--help|-h]"
      echo "  --debug, -d    Enable debug output"
      echo "  --help, -h     Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Debug helper
debug_echo() {
  if [ "$DEBUG" -eq 1 ]; then
    printf '\033[1;33m[DEBUG]\033[0m %s\n' "$*" >&2
  fi
}

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

debug_echo "Script started with DEBUG=$DEBUG"

# Check if smartctl is available
if ! command -v smartctl &> /dev/null; then
  green_echo "[!] smartctl not found. Installing smartmontools..."
  sudo apt update -y
  sudo apt install -y smartmontools
fi

# Get power-on hours for a drive
get_power_on_hours() {
  local drive="$1"
  local hours
  
  # Check if SMART is supported and enabled
  if ! sudo smartctl -i "$drive" 2>/dev/null | grep -q "SMART support is:.*Enabled\|Available"; then
    debug_echo "$drive: SMART not supported"
    return 1
  fi
  
  hours=$(sudo smartctl -A "$drive" 2>/dev/null | awk '$2 == "Power_On_Hours" {print $10}')
  
  if [[ -n "$hours" ]]; then
    echo "$hours"
    return 0
  else
    debug_echo "$drive: Power_On_Hours attribute not found"
    return 1
  fi
}

# Check and display drive info
check_drive() {
  local drive="$1"
  local hours
  
  if hours=$(get_power_on_hours "$drive" 2>&1); then
    local days=$((hours / 24))
    local years=$((days / 365))
    green_echo "$drive : $hours hours ($days days / ~$years years)"
  else
    green_echo "$drive : Power_On_Hours not available"
  fi
}

# Discover all physical drives
discover_drives() {
  local drives=()
  
  debug_echo "Searching for drives..."
  
  # Find SATA/USB drives
  for dev in /dev/sd?; do
    if [ -b "$dev" ]; then
      debug_echo "Found SATA/USB: $dev"
      drives+=("$dev")
    fi
  done
  
  # Find NVMe drives
  for dev in /dev/nvme?n?; do
    if [ -b "$dev" ]; then
      debug_echo "Found NVMe: $dev"
      drives+=("$dev")
    fi
  done
  
  debug_echo "Total drives found: ${#drives[@]}"
  printf '%s\n' "${drives[@]}"
}

# Get drive size safely
get_drive_size() {
  local drive="$1"
  local bytes
  
  if bytes=$(sudo blockdev --getsize64 "$drive" 2>/dev/null); then
    if [[ "$bytes" -gt 0 ]] 2>/dev/null; then
      printf "%.1fG" "$(echo "scale=1; $bytes/1024/1024/1024" | bc)"
    else
      echo "?"
    fi
  else
    echo "?"
  fi
  return 0
}

# Get drive model safely
get_drive_model() {
  local drive="$1"
  local model
  
  if model=$(sudo smartctl -i "$drive" 2>/dev/null | grep -E "Device Model|Model Number" | head -1 | cut -d: -f2); then
    model=$(echo "$model" | xargs)
    if [[ -n "$model" ]]; then
      echo "$model"
    else
      echo "Unknown"
    fi
  else
    echo "Unknown"
  fi
  return 0
}

# Non-interactive mode
if [ ! -t 0 ]; then
  debug_echo "Non-interactive mode"
  green_echo "[*] Checking all drives..."
  echo "────────────────────────────────────────────────────────────────────────────────"
  
  mapfile -t drives < <(discover_drives)
  
  if [ "${#drives[@]}" -eq 0 ]; then
    green_echo "[!] No drives found"
    exit 1
  fi
  
  for drive in "${drives[@]}"; do
    check_drive "$drive"
  done
  
  echo "────────────────────────────────────────────────────────────────────────────────"
  green_echo "[+] Complete"
  exit 0
fi

# Interactive menu
show_menu() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                    Drive Power-On Hours Check                                 ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  mapfile -t drives < <(discover_drives)
  
  if [ "${#drives[@]}" -eq 0 ]; then
    green_echo "[!] No drives found"
    exit 1
  fi
  
  local i=1
  for drive in "${drives[@]}"; do
    debug_echo "Getting info for drive $i: $drive"
    
    local size model
    size=$(get_drive_size "$drive")
    debug_echo "Size: $size"
    
    model=$(get_drive_model "$drive")
    debug_echo "Model: $model"
    
    printf "  %2d) %-15s %-10s %s\n" "$i" "$drive" "$size" "$model"
    i=$((i + 1))
  done
  
  echo
  echo "   a) Check all drives"
  echo "   0) Exit"
  echo
}

# Main loop
debug_echo "Interactive mode"

while true; do
  show_menu
  mapfile -t drives < <(discover_drives)
  
  read -rp "Enter choice (number, 'a' for all, or '0' to exit): " choice
  
  if [[ "$choice" == "0" ]]; then
    green_echo "Exiting. Goodbye!"
    break
  elif [[ "$choice" == "a" ]] || [[ "$choice" == "A" ]]; then
    echo
    green_echo "[*] Checking ${#drives[@]} drive(s)..."
    echo "────────────────────────────────────────────────────────────────────────────────"
    for drive in "${drives[@]}"; do
      check_drive "$drive"
    done
    echo "────────────────────────────────────────────────────────────────────────────────"
    echo
    read -rp "Press Enter to continue..."
  elif [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#drives[@]} )); then
    drive="${drives[$((choice-1))]}"
    echo
    check_drive "$drive"
    echo
    read -rp "Press Enter to continue..."
  elif [[ "$choice" =~ ^[0-9,\ ]+$ ]]; then
    IFS=',' read -ra selections <<< "$choice"
    selected_drives=()
    for sel in "${selections[@]}"; do
      sel=$(echo "$sel" | xargs)
      if [[ "$sel" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#drives[@]} )); then
        selected_drives+=("${drives[$((sel-1))]}")
      fi
    done
    
    if [ "${#selected_drives[@]}" -gt 0 ]; then
      echo
      green_echo "[*] Checking ${#selected_drives[@]} drive(s)..."
      echo "────────────────────────────────────────────────────────────────────────────────"
      for drive in "${selected_drives[@]}"; do
        check_drive "$drive"
      done
      echo "────────────────────────────────────────────────────────────────────────────────"
    else
      green_echo "[!] No valid drives selected"
    fi
    echo
    read -rp "Press Enter to continue..."
  else
    green_echo "[!] Invalid choice"
    sleep 1
  fi
done

exit 0

