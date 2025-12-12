#!/bin/bash

# Simple test script for custom script addition
# Location: /home/adam/lv_linux_learn/examples/hello_test.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../includes/main.sh"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Hello Test Script                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

green_echo "[*] This is a test script added via menu.sh"
green_echo "[*] Script location: $(realpath "$0")"
green_echo "[*] Current date: $(date)"

echo
green_echo "[✓] Test completed successfully!"
echo

read -rp "Press Enter to continue..."
