#!/bin/bash
# This script displays the current date and time.
# Demonstrates using the 'date' command with various formats.

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

echo "═══════════════════════════════════════════════════════════════════════════════"
green_echo "Exercise 2: Show Date"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] The 'date' command can display time in many formats:"
echo
echo "    Default format:"
echo "    $(date)"
echo
echo "    ISO 8601 format (YYYY-MM-DD HH:MM:SS):"
echo "    $(date '+%Y-%m-%d %H:%M:%S')"
echo
echo "    Unix timestamp (seconds since 1970-01-01):"
echo "    $(date '+%s')"
echo
echo "    Day of week, Month Day, Year:"
echo "    $(date '+%A, %B %d, %Y')"
echo
echo "    12-hour format with AM/PM:"
echo "    $(date '+%I:%M:%S %p')"
echo
green_echo "[+] Date command completed successfully."
echo
echo "Press Enter to continue..."
read -r
