#!/bin/bash
# This script prompts the user to enter a directory name and creates it.
# Demonstrates user input with 'read' and directory creation with 'mkdir'.

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
green_echo "Exercise 4: Make Directory"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This exercise demonstrates:"
echo "    • Reading user input with 'read' command"
echo "    • Creating directories with 'mkdir' command"
echo "    • Checking if directories already exist"
echo "    • Error handling"
echo
green_echo "[*] Current directory: $(pwd)"
echo

read -rp "Enter new directory name (e.g., 'test_dir'): " dirname

if [ -z "$dirname" ]; then
  echo "[!] Error: Directory name cannot be empty."
  echo
  echo "Press Enter to continue..."
  read -r
  exit 1
fi

if [ -d "$dirname" ]; then
  echo "[!] Warning: Directory '$dirname' already exists."
  echo "    Location: $(pwd)/$dirname"
else
  if mkdir "$dirname" 2>/dev/null; then
    green_echo "[+] Success! Directory '$dirname' created."
    echo "    Full path: $(pwd)/$dirname"
    echo
    green_echo "[*] Verifying directory was created:"
    ls -ld "$dirname"
  else
    echo "[!] Error: Failed to create directory '$dirname'."
    echo "    Check permissions and try again."
  fi
fi

echo
echo "Press Enter to continue..."
read -r
