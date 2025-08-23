#!/bin/bash
# This can be used to remove hamachi

# Includes
source includes/main.sh

green_echo "[!] Starting uninstaller!"
read -p "Press Enter to continue..." # Waits for Enter key press

green_echo "[*] Removing logmein-hamachi..."
sudo apt purge -y --autoremove logmein-hamachi 

green_echo "[*] Removing config files..."
sudo rm -rf /var/lib/logmein-hamachi

green_echo "[*] Removing desktop icon..."
rm -rf $HOME/.lv_connect
rm $HOME/Desktop/ShowMeshnetInfo.desktop
rm $HOME/.lv_connect/ShowMeshnetInfo.sh
rm $HOME/Desktop/ShowHamachiInfo.desktop
green_echo "[*] Removing logmein-hamachi config file..."
rm /var/lib/logmein-hamachi/h2-engine-override.cfg

green_echo "Uninstall completed!"