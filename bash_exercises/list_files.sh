#!/bin/bash
# This script lists all files in the current directory.
# Demonstrates the 'ls' command with various options.

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
green_echo "Exercise 3: List Files"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] Current working directory:"
echo "    $(pwd)"
echo
green_echo "[*] Basic file listing (ls):"
echo
ls
echo
green_echo "[*] Detailed listing with permissions (ls -lh):"
echo
ls -lh
echo
green_echo "[*] Show hidden files too (ls -lha):"
echo
ls -lha | head -n 10
if [ "$(ls -lha | wc -l)" -gt 10 ]; then
  echo "    ... (showing first 10 entries)"
fi
echo
green_echo "[+] File listing completed."
green_echo "[*] Tip: Use 'ls -lha' to see all files including hidden ones (starting with .)"
echo
echo "Press Enter to continue..."
read -r
