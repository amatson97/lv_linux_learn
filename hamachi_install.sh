#!/bin/bash
# This will install hamachi vpn and log you in to the Linux Learn network.
#You do not have permission to control the hamachid daemon.
#You can run 'hamachi' as root, or you can add your login name to the file
#'/var/lib/logmein-hamachi/h2-engine-override.cfg'
#and restart the daemon with
#sudo /etc/init.d/logmein-hamachi restart
#Example:
#Ipc.User      <login name>

# Includes
source includes/main.sh
DESKTOP_LAUNCHER="$HOME/Desktop/ShowHamachiInfo.desktop"

set -e

# Ensure the system is up-to-date
green_echo "[*] Updating..."
sudo apt update

# Download the latest Hamachi .deb package from the official site
green_echo "[*] Downloading hamachi installer..."
wget -O logmein-hamachi.deb "https://vpn.net/installers/logmein-hamachi_2.1.0.203-1_amd64.deb"

# Install the downloaded package
green_echo "[*] Installing hamachi..."
sudo dpkg -i logmein-hamachi.deb

# Log in to Hamachi
green_echo "[*] Logging in to hamachi..."
sleep 10
sudo hamachi login


# Join the specified network
green_echo "[*] Joining Hamach hetwork..."
sudo hamachi join 496-925-380
sleep 1

# Cleaning up install
sudo rm logmein-hamachi.deb

green_echo "[!] Hamachi should now be installed, logged in, and joined to network 496-925-380!"
green_echo "[*] Adding $USER to /var/lib/logmein-hamachi/h2-engine-override.cfg..."

cat <<EOF | sudo tee /var/lib/logmein-hamachi/h2-engine-override.cfg > /dev/null
Ipc.User      $USER
EOF

sleep 1

green_echo "[*] Restarting logmein-hamachi..."
sudo /etc/init.d/logmein-hamachi restart

create_hamachi_info_desktop_icon