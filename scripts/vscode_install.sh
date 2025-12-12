#!/bin/bash
# Install Visual Studio Code
# Description: Installs Microsoft Visual Studio Code editor with extensions support.
# Official Site: https://code.visualstudio.com/

set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Starting Visual Studio Code installation..."
    
    # Check if already installed
    if command -v code >/dev/null 2>&1; then
        green_echo "[!] VS Code is already installed: $(code --version | head -1)"
        read -p "Reinstall anyway? (y/N): " reinstall
        if [[ ! "$reinstall" =~ ^[Yy]$ ]]; then
            green_echo "[*] Installation cancelled."
            exit 0
        fi
    fi
    
    # Install dependencies
    green_echo "[*] Installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y wget gpg apt-transport-https
    
    # Add Microsoft GPG key
    green_echo "[*] Adding Microsoft GPG key..."
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
    sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
    rm -f packages.microsoft.gpg
    
    # Add VS Code repository
    green_echo "[*] Adding VS Code repository..."
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | \
        sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
    
    # Install VS Code
    green_echo "[*] Installing Visual Studio Code..."
    sudo apt-get update
    sudo apt-get install -y code
    
    # Verify installation
    if command -v code >/dev/null 2>&1; then
        version=$(code --version | head -1)
        green_echo "[+] VS Code installed successfully: $version"
        green_echo "[*] You can launch it with: code"
    else
        echo "[!] Installation completed but 'code' command not found."
        echo "[!] You may need to restart your terminal or log out and back in."
        exit 1
    fi
    
    # Optional: Install popular extensions
    read -p "Install recommended extensions? (Y/n): " install_ext
    if [[ ! "$install_ext" =~ ^[Nn]$ ]]; then
        green_echo "[*] Installing recommended extensions..."
        code --install-extension ms-python.python
        code --install-extension ms-vscode.cpptools
        code --install-extension dbaeumer.vscode-eslint
        code --install-extension esbenp.prettier-vscode
        code --install-extension eamodio.gitlens
        green_echo "[+] Extensions installed."
    fi
    
    green_echo "[+] Installation complete!"
    green_echo "[*] Launch VS Code with: code"
    green_echo "[*] Or search for 'Visual Studio Code' in your applications menu."
}

main "$@"
