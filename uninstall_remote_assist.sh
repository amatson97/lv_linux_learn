#!/bin/bash
# Uninstall script for remote assistance

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

green_echo "[!] Starting uninstaller!"
read -p "Press Enter to continue..." # Waits for Enter key press

green_echo "[!] Removing $USER from nordvpn group!"
sudo gpasswd -d $USER nordvpn
green_echo "[✓] Removed $USER from nordvpn group!"
sleep 1

green_echo "[!] Removing nordvpn group!"
sudo groupdel nordvpn
green_echo "[✓] Removed nordvpn group!"
sleep 1

green_echo "[!] Uninstalling nordvpn!"
sudo apt-get remove nordvpn -y
green_echo "[✓] Removed nordvpn!"
sleep 1

green_echo "[!] Removing installation files!"
rm $HOME/Desktop/ShowMeshnetInfo.desktop
rm $HOME/.lv_connect/ShowMeshnetInfo.sh
green_echo "[✓] Desktop icon removed!"
rm -rf $HOME/.lv_connect
green_echo "[✓] Application Directory removed!"
sleep 1

green_echo "[✓] Uninstall complete!"
read -p "Press Enter to exit..." # Waits for Enter key press