#!/bin/bash
# Description: Loop tutorial - Learn 'for' loops and iteration concepts
#
# Educational script demonstrating loop constructs in bash scripting.
# Shows different types of 'for' loops, sequence generation, and iteration
# patterns. Essential for learning control flow and repetitive operations.

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
green_echo "Exercise 5: Print Numbers"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo
green_echo "[*] This exercise demonstrates:"
echo "    • Using 'for' loops in bash"
echo "    • Brace expansion {1..10}"
echo "    • Iterating through sequences"
echo "    • Variable usage in loops"
echo
green_echo "[*] Printing numbers from 1 to 10:"
echo

for i in {1..10}; do
  echo "    Number: $i"
done

echo
green_echo "[+] Loop completed successfully!"
echo
green_echo "[*] Other loop examples:"
echo "    • for i in {1..10}; do ... done    # Brace expansion"
echo "    • for i in \$(seq 1 10); do ... done  # Using seq command"
echo "    • for ((i=1; i<=10; i++)); do ... done  # C-style loop"
echo
echo "Press Enter to continue..."
read -r
