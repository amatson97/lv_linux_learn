#!/bin/bash
# checks for an removes all vpns

#functions
source includes/main.sh

#call functions
remove_if_installed_zerotier "zerotier-one"
remove_if_installed_nord "nordvpn"
remove_if_installed_hamachi "logmein-hamachi"
remove_files