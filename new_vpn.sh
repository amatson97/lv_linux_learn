#!/bin/bash
# https://my.zerotier.com/network/8bd5124fd60a971f
# Installs zerotier and joins the Linux Learn Network.
# Removes conflicting VPNs (NordVPN, LogMeIn Hamachi) if present.

# Includes
source includes/main.sh

# Check and uninstall conflicting VPN software
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"

sleep 5

# Install ZeroTier
green_echo "[*] Installing ZeroTier..."
curl -s https://install.zerotier.com | sudo bash

# Join network
green_echo "[*] Joining Linux Learn Network..."
sleep 2

# Join zerotier network.
sudo zerotier-cli join 8bd5124fd60a971f

green_echo "[✔] Install complete!"
