#!/bin/bash
# https://my.zerotier.com/network/8bd5124fd60a971f
# Installs zerotier and joins the Linux Learn Network.
# Removes conflicting VPNs (NordVPN, LogMeIn Hamachi) if present.

#nettowrk ID
ZEROTIER_NETWORK=8bd5124fd60a971f

#functions
source includes/main.sh

#calling functions
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"
sleep 5
install_zerotier