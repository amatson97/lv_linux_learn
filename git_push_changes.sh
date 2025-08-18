#!/bin/bash
# Script to commit changes to github

# Includes
source includes/main.sh

green_echo "[*] Stagging changes..."
git add .
sleep 1

green_echo "[*] Commiting changes..."
sudo git commit
sleep 1

green_echo "[!] About to push changes..."
read -p "Press Enter to continue..." # Waits for Enter key press
git push