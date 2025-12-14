#!/bin/bash
# Description: Custom script demo - Learn script integration and path handling
#
# Demonstration script for the Custom Script Addition feature in the menu system.
# Shows path detection, environment variables, and integration with the
# script management interface. Educational tool for understanding script organization.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared functions using absolute path
if [ -f "$SCRIPT_DIR/includes/main.sh" ]; then
    source "$SCRIPT_DIR/includes/main.sh"
elif [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    source "$HOME/lv_linux_learn/includes/main.sh"
else
    # Fallback green_echo if not found
    green_echo() {
        echo -e "\033[0;32m$1\033[0m"
    }
fi

green_echo "╔════════════════════════════════════════╗"
green_echo "║   Test Custom Script                   ║"
green_echo "╚════════════════════════════════════════╝"

green_echo "[*] This is a custom script example!"
green_echo "[*] It demonstrates the Custom Script Addition feature."
green_echo "[*] You can:"
green_echo "    • Add custom scripts using the '+' button on any tab"
green_echo "    • Edit custom scripts by right-clicking them"
green_echo "    • Delete custom scripts from the right-click menu"
green_echo "    • Run custom scripts just like built-in ones"

echo ""
green_echo "[✓] Script execution completed!"
echo ""
read -p "Press Enter to continue..."
