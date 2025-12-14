#!/bin/bash
# Uninstall Visual Studio Code
# Description: Removes VS Code, optionally removes configuration and extensions.

set -euo pipefail

# Includes
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES_DIR="$SCRIPT_DIR/../includes"
if [ -f "$INCLUDES_DIR/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$INCLUDES_DIR/main.sh"
elif [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    # shellcheck source=/dev/null
    source "$HOME/lv_linux_learn/includes/main.sh"
else
    echo "Error: Could not find includes/main.sh"
    exit 1
fi

main() {
    green_echo "[*] Visual Studio Code Uninstaller"
    echo ""
    
    # Check if VS Code is installed
    if ! check_installed "code"; then
        green_echo "[!] VS Code is not installed."
        exit 0
    fi
    
    green_echo "[!] This will remove Visual Studio Code from your system."
    echo ""
    
    # Confirm uninstallation
    if ! confirm_uninstall "Visual Studio Code"; then
        green_echo "[*] Uninstallation cancelled."
        exit 0
    fi
    
    # Remove VS Code package
    green_echo "[*] Removing Visual Studio Code..."
    sudo apt-get remove -y code
    sudo apt-get autoremove -y
    
    # Remove repository
    green_echo "[*] Removing VS Code repository..."
    sudo rm -f /etc/apt/sources.list.d/vscode.list
    sudo rm -f /etc/apt/keyrings/packages.microsoft.gpg
    
    # Update package cache
    sudo apt-get update
    
    # Ask about user data
    echo ""
    green_echo "[?] Remove VS Code user data and extensions?"
    echo "    This includes:"
    echo "    • Extensions (~/.vscode/extensions)"
    echo "    • Settings and configurations (~/.config/Code)"
    echo "    • Cached data (~/.cache/vscode)"
    echo ""
    read -p "Remove user data? (y/N): " remove_data
    
    if [[ "$remove_data" =~ ^[Yy]$ ]]; then
        green_echo "[*] Removing user data and extensions..."
        rm -rf ~/.vscode
        rm -rf ~/.config/Code
        rm -rf ~/.cache/vscode
        green_echo "[+] User data removed."
    else
        green_echo "[*] User data preserved in ~/.vscode and ~/.config/Code"
    fi
    
    green_echo "[+] Visual Studio Code has been uninstalled."
}

main "$@"
