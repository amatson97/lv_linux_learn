#!/bin/bash
# checks for an removes all vpns

# Includes
source includes/main.sh

# Check and uninstall conflicting VPN software
remove_if_installed_zerotier "zerotier-one"
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"


