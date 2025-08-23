#!/bin/bash
# This will install hamachi vpn and log you in to the Linux Learn network.
# This script is now deprecated.
source includes/main.sh
install_hamachi
create_hamachi_info_desktop_icon
sudo rm logmein-hamachi.deb