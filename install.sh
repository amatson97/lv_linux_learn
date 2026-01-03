#!/bin/bash
# lv_linux_learn Quick Start Installer for Ubuntu 24.04 LTS (v2.2.6+ compatible)[4]
set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}=== lv_linux_learn Quick Start Installer ===${NC}"
echo "Dual interface: GUI (menu.py) + CLI (menu.sh)"

# Check Ubuntu 24.04
if ! lsb_release -d 2>/dev/null | grep -q "24.04"; then
    echo -e "${YELLOW}Warning: Not Ubuntu 24.04${NC}"
    read -p "Continue? (y/N): " -r || exit 1
    [[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

# Install dependencies
echo "Installing dependencies..."
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv libgtk-4-1 libgtk-4-dev libadwaita-1-0 curl wget

# Setup directory
LV_DIR="$HOME/lv_linux_learn"
[[ -d "$LV_DIR" ]] && { echo -e "${YELLOW}Removing $LV_DIR...${NC}"; rm -rf "$LV_DIR"; }
mkdir -p "$LV_DIR"
cd "$LV_DIR"

# Clone repo
echo "Cloning repository..."
git clone https://github.com/amatson97/lv_linux_learn.git .
echo -e "${GREEN}Cloned successfully${NC}"

# Make executable
chmod +x menu.sh menu.py dev_tools/*.sh 2>/dev/null || true

# Verify core files exist after clone
for file in menu.sh menu.py lib/repository.py lib/script_execution.py; do
    [[ ! -f "$file" ]] && { echo -e "${RED}ERROR: Missing $file${NC}"; exit 1; }
done
echo -e "${GREEN}Core files verified: menu.py/sh, lib/ modules${NC}"

echo -e "\n${GREEN}=== SUCCESS! ===${NC}"
echo "Commands:"
echo "  cd $LV_DIR && ./menu.sh    # CLI"
echo "  cd $LV_DIR && ./menu.py    # GUI (GTK)"

# Auto-launch
if [[ -n "${DISPLAY:-}" && -x "$(command -v python3)" ]]; then
    read -p "Launch GUI? (y/N): " -r
    [[ $REPLY =~ ^[Yy]$ ]] && ./menu.py
else
    read -p "Launch CLI? (y/N): " -r
    [[ $REPLY =~ ^[Yy]$ ]] && ./menu.sh
fi

echo -e "${GREEN}Done! cd $LV_DIR to start${NC}"
