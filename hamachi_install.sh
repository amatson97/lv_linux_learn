#!/bin/bash
# sudo rm -rf /var/lib/logmein-hamachi
# sudo apt purge --autoremove logmein-hamachi

# Includes
source includes/main.sh

set -e

# Ensure the system is up-to-date
green_echo "[*] Updating..."
sudo apt update

# Download the latest Hamachi .deb package from the official site
green_echo "[*] Downloading Hamachi installer..."
wget -O logmein-hamachi.deb "https://vpn.net/installers/logmein-hamachi_2.1.0.203-1_amd64.deb"

# Install the downloaded package
green_echo "[*] Installing hamachi..."
sudo dpkg -i logmein-hamachi.deb

# Log in to Hamachi
green_echo "[*] Logging in to Hamachi..."
sleep 10
sudo hamachi login


# Join the specified network
green_echo "[*] Joining Hamach Network..."
sudo hamachi join 496-925-380

# Cleaning up install
sudo rm logmein-hamachi.deb

echo "Hamachi should now be installed, logged in, and joined to network 496-925-380!"