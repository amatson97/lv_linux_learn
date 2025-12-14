#!/bin/bash
# Description: Install Sublime Text editor and Sublime Merge git client
#
# Installs both Sublime Text (premium code editor) and Sublime Merge
# (visual git client) from official Sublime HQ repository. Handles repository
# setup, GPG keys, and provides complete text editing and version control tools.
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Check if already installed
if command -v subl &> /dev/null && command -v smerge &> /dev/null; then
  green_echo "[+] Sublime Text and Sublime Merge already installed"
  exit 0
fi

green_echo "[*] Installing GPG key..."
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo tee /etc/apt/keyrings/sublimehq-pub.asc > /dev/null

green_echo "[*] Adding Sublime stable channel..."
echo -e 'Types: deb\nURIs: https://download.sublimetext.com/\nSuites: apt/stable/\nSigned-By: /etc/apt/keyrings/sublimehq-pub.asc' | sudo tee /etc/apt/sources.list.d/sublime-text.sources > /dev/null

green_echo "[*] Updating package lists and installing Sublime Text and Sublime Merge..."
sudo apt-get update -y
sudo apt-get install -y apt-transport-https sublime-text sublime-merge

green_echo "[+] Sublime Text and Sublime Merge installed successfully"
exit 0