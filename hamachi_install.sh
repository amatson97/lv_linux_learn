#!/bin/bash
# This will install hamachi vpn and log you in to the Linux Learn network.
# This script is now deprecated.

#functions
source includes/main.sh

#call functions
install_hamachi
create_hamachi_info_desktop_icon
sudo rm logmein-hamachi.deb