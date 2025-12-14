#!/bin/bash
# Description: Hello World tutorial - Your first bash script
#
# The classic "Hello, World!" program adapted for bash scripting education.
# Perfect introduction to script structure, shebang lines, comments, and
# basic output commands. Essential first step for learning shell scripting.

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
green_echo "Exercise 1: Hello World"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This is the classic first program - it demonstrates:"
echo "    • Basic script structure (#!/bin/bash shebang)"
echo "    • Using the 'echo' command to print text"
echo "    • Running commands in sequence"
echo
green_echo "[*] Output:"
echo
echo "    Hello, World!"
echo
green_echo "[+] Success! You've run your first bash script."
echo
echo "Press Enter to continue..."
read -r
