#!/bin/bash
# Script to commit changes to GitHub

# Includes
source includes/main.sh

# Check if git user.name and user.email are configured
if ! git config --get user.name >/dev/null || ! git config --get user.email >/dev/null; then
  green_echo "[!] Git is not configured. Running git_setup.sh..."
  ./git_setup.sh
fi

green_echo "[*] Staging changes..."
git add .
sleep 1

green_echo "[*] Committing changes..."
sudo git commit
sleep 1

green_echo "[!] About to push changes..."
read -p "Press Enter to continue..." # Wait for Enter key press
git push
