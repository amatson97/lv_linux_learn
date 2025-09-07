#!/bin/bash
# Install flatpak, a useful software repository. Has its own software store as well.

# Includes
source includes/main.sh

green_echo "[*] Installing flatpak..."
sudo apt install flatpak -y

green_echo "[*] Installing gnome-software-plugin-flatpak..."
sudo apt install gnome-software-plugin-flatpak -y

green_echo "[*] Adding flathub..."
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
