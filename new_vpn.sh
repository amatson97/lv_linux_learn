#!/bin/bash
# https://my.zerotier.com/network/8bd5124fd60a971f
# Make sure to run uninstall of current vpn.
# sudo apt remove logmein-hamachi nordvpn

# Includes
source includes/main.sh

green_echo "[*] Installing zerotier..."
curl -s https://install.zerotier.com | sudo bash


green_echo "[*] Joing Linux Learn Network..."
sleep 2
sudo zerotier-cli join 8BD5124FD60A971F