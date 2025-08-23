#!/bin/bash
# https://my.zerotier.com/network/8bd5124fd60a971f
# Installs zerotier and joins the Linux Learn Network.
# Removes conflicting VPNs (NordVPN, LogMeIn Hamachi) if present.

# Includes
source includes/main.sh

# Function to check and remove a package if installed
remove_if_installed() {
    local pkg="$1"
    if dpkg -l | grep -q "^ii\s*$pkg"; then
        green_echo "[*] $pkg detected, removing..."
        sudo apt-get remove -y --purge "$pkg"
        sudo apt-get autoremove -y
        green_echo "[✔] $pkg removed."
        green_echo "[*]Removing desktop icons..."
		rm $HOME/Desktop/ShowHamachiInfo.desktop
		rm $HOME/.lv_connect/ShowHamachiInfo.sh
		rm /var/lib/logmein-hamachi/h2-engine-override.cfg
		rm $HOME/Desktop/ShowMeshnetInfo.desktop
		rm $HOME/.lv_connect/ShowMeshnetInfo.sh
		rm -rf $HOME/.lv_connect
    else
        green_echo "[*] $pkg not installed, skipping."
    fi
}

# Check and uninstall conflicting VPN software
remove_if_installed "nordvpn"
remove_if_installed "logmein-hamachi"

sleep 5

# Install ZeroTier
green_echo "[*] Installing ZeroTier..."
curl -s https://install.zerotier.com | sudo bash

# Join network
green_echo "[*] Joining Linux Learn Network..."
sleep 2
sudo zerotier-cli join 8bd5124fd60a971f

green_echo "[✔] Install complete!"
