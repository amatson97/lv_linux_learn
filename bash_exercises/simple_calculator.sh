#!/bin/bash
# Description: Interactive calculator - Learn arithmetic and input validation
#
# Educational script for learning basic arithmetic operations and user input handling.
# Demonstrates numeric input validation, error handling, and mathematical operations
# in bash scripting. Perfect introduction to interactive script development.

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
green_echo "Exercise 6: Simple Calculator"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This exercise demonstrates:"
echo "    • Reading numeric input from users"
echo "    • Arithmetic operations in bash"
echo "    • Using \$(( )) for calculations"
echo "    • Input validation"
echo

read -rp "Enter first number: " a
read -rp "Enter second number: " b

# Validate input
if ! [[ "$a" =~ ^-?[0-9]+$ ]] || ! [[ "$b" =~ ^-?[0-9]+$ ]]; then
  echo "[!] Error: Please enter valid integers only."
  echo
  echo "Press Enter to continue..."
  read -r
  exit 1
fi

echo
green_echo "[*] Performing calculations:"
echo

sum=$((a + b))
echo "    $a + $b = $sum"

diff=$((a - b))
echo "    $a - $b = $diff"

prod=$((a * b))
echo "    $a × $b = $prod"

if [ "$b" -ne 0 ]; then
  div=$((a / b))
  echo "    $a ÷ $b = $div (integer division)"
else
  echo "    $a ÷ $b = undefined (division by zero)"
fi

echo
green_echo "[+] Calculations completed!"
echo
echo "Press Enter to continue..."
read -r