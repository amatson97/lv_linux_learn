#!/bin/bash
# Description: File analysis tutorial - Learn 'wc' command and file operations
#
# Educational script for learning file analysis using the 'wc' (word count) command.
# Teaches file existence validation, user input handling, and text file statistics.
# Demonstrates essential file processing concepts in shell scripting.
# Line added: to Test checksum change for manifest.

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
green_echo "Exercise 8: Count Lines"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This exercise demonstrates:"
echo "    • Using 'wc' (word count) command"
echo "    • Counting lines with 'wc -l'"
echo "    • File existence checking"
echo "    • Command substitution \$(command)"
echo
green_echo "[*] Current directory: $(pwd)"
echo
green_echo "[*] Available files in current directory:"
ls -1 2>/dev/null | head -n 10 || echo "    (No files found)"
echo

read -rp "Enter filename to count lines: " filename

if [[ ! -f "$filename" ]]; then
  echo "[!] Error: File '$filename' does not exist."
  echo "    Make sure the file exists in: $(pwd)"
  echo
  echo "Press Enter to continue..."
  read -r
  exit 1
fi

echo
green_echo "[*] Analyzing file: $filename"
echo

lines=$(wc -l < "$filename")
words=$(wc -w < "$filename")
chars=$(wc -m < "$filename")
bytes=$(wc -c < "$filename")

echo "    Lines:      $lines"
echo "    Words:      $words"
echo "    Characters: $chars"
echo "    Bytes:      $bytes"

echo
green_echo "[+] File analysis completed!"
echo
green_echo "[*] The 'wc' command can count:"
echo "    • wc -l  : lines"
echo "    • wc -w  : words"
echo "    • wc -m  : characters"
echo "    • wc -c  : bytes"
echo
echo "Press Enter to continue..."
read -r
