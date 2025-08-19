#!/bin/bash

# Includes
source includes/main.sh

green_echo "[*] Preparing to pull down latest changes..."
sleep 1

green_echo "[*] Running git pull..."
sudo git pull

green_echo "[!] Complete..."
