#!/bin/bash
# This script prompts for a filename and a word, then shows all lines containing that word.
# Demonstrates the 'grep' command for pattern matching and text searching.

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
green_echo "Exercise 7: Find Word"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This exercise demonstrates:"
echo "    • Using 'grep' to search for patterns in files"
echo "    • Case-insensitive searching (-i flag)"
echo "    • Line number display (-n flag)"
echo "    • File existence checking with [[ -f ]]"
echo
green_echo "[*] Current directory: $(pwd)"
echo
green_echo "[*] Available text files in current directory:"
ls -1 *.txt *.md *.sh 2>/dev/null | head -n 10 || echo "    (No .txt, .md, or .sh files found)"
echo

read -rp "Enter filename to search: " filename

if [[ ! -f "$filename" ]]; then
  echo "[!] Error: File '$filename' not found."
  echo "    Make sure the file exists in: $(pwd)"
  echo
  echo "Press Enter to continue..."
  read -r
  exit 1
fi

read -rp "Enter word to search for: " word

if [ -z "$word" ]; then
  echo "[!] Error: Search word cannot be empty."
  echo
  echo "Press Enter to continue..."
  read -r
  exit 1
fi

echo
green_echo "[*] Searching for '$word' in '$filename' (case-insensitive):"
echo

if grep -in "$word" "$filename"; then
  echo
  match_count=$(grep -ic "$word" "$filename")
  green_echo "[+] Found $match_count match(es) for '$word'"
else
  echo "    (No matches found)"
  echo
  echo "[!] The word '$word' was not found in '$filename'"
fi

echo
green_echo "[*] Tip: Use 'grep -r' to search recursively in directories"
echo
echo "Press Enter to continue..."
read -r
