#!/bin/bash
#Install chrome

# Includes
source includes/main.sh

# install dependencies
sudo apt install wget -y

# Download .deb file
green_echo "[*] Downloading google-chrome-stable_current_amd64.deb..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install
green_echo "[*] Installing google-chrome-stable_current_amd64.deb..."
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Clean up
green_echo "[!] Cleaning up files..."
rm google-chrome-stable_current_amd64.deb