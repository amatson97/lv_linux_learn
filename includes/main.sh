#!/bin/bash

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

user_in_nordvpn_group() {
  id -nG "$USER" | grep -qw "nordvpn"
}

install_hamachi(){
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

  green_echo "[!] Hamachi should now be installed, logged in, and joined to network 496-925-380!"
  green_echo "[*] Adding $USER to /var/lib/logmein-hamachi/h2-engine-override.cfg..."

  cat <<EOF | sudo tee /var/lib/logmein-hamachi/h2-engine-override.cfg > /dev/null
  Ipc.User      $USER
  EOF

  sleep 1

  green_echo "[*] Restarting logmein-hamachi..."
  sudo /etc/init.d/logmein-hamachi restart
}

create_meshnet_info_desktop_icon() {
  mkdir $HOME/.lv_connect
  cat > "$HOME/.lv_connect/ShowMeshnetInfo.sh" <<'EOF'
#!/bin/bash

MESHNET_HOST=$(nordvpn meshnet peer list | awk '
  BEGIN {found=0}
  /^This device:/ {found=1; next}
  found && /^Hostname:/ {print $2; exit}
')

enabled=$(gsettings get org.gnome.desktop.remote-desktop.rdp enable)
if [ "$enabled" != "true" ]; then
  zenity --info --title="Enable Remote Desktop" --text="
GNOME Remote Desktop (RDP) is currently disabled.

To enable remote assistance:

1. Open Settings.
2. Go to System → Remote Desktop.
3. Enable 'Desktop Sharing'.
4. Enable 'Remote Control'.
5. Set a password.

After enabling, use the hostname:$MESHNET_HOST to connect remotely.
"
  exit 1
fi

MESHNET_HOST=$(nordvpn meshnet peer list | awk '
  BEGIN {found=0}
  /^This device:/ {found=1; next}
  found && /^Hostname:/ {print $2; exit}
')

if [[ -z "$MESHNET_HOST" ]]; then
  zenity --error --text="Meshnet hostname not found. Is NordVPN running and Meshnet enabled?"
  exit 1
fi

zenity --info --title="Remote Desktop Details" --text="Connect using: $MESHNET_HOST"
EOF

  chmod +x "$HOME/.lv_connect/ShowMeshnetInfo.sh"

  cat > "$DESKTOP_LAUNCHER" <<EOF
[Desktop Entry]
Name=Remote Desktop Info
Comment=Show Meshnet hostname and Remote Desktop instructions
Exec=$HOME/.lv_connect/ShowMeshnetInfo.sh
Icon=network-workgroup
Terminal=false
Type=Application
Categories=Network;Utility;
EOF

  chmod +x "$DESKTOP_LAUNCHER"
  gio set "$DESKTOP_LAUNCHER" metadata::trusted true || green_echo "Note: You may need to right-click the launcher and allow launching."
  green_echo "[+] Created desktop launcher at $DESKTOP_LAUNCHER"
}

create_hamachi_info_desktop_icon() {
  mkdir $HOME/.lv_connect
  cat > "$HOME/.lv_connect/ShowHamachiInfo.sh" <<'EOF'
#!/bin/bash

HAM_IP=$(ip address show dev ham0 | awk '/inet / {print $2}' | cut -d'/' -f1)

enabled=$(gsettings get org.gnome.desktop.remote-desktop.rdp enable)
if [ "$enabled" != "true" ]; then
  zenity --info --title="Enable Remote Desktop" --text="
GNOME Remote Desktop (RDP) is currently disabled.

To enable remote assistance:

1. Open Settings.
2. Go to System → Remote Desktop.
3. Enable 'Desktop Sharing'.
4. Enable 'Remote Control'.
5. Set a password.

After enabling, use the hostname:$HAM_IP to connect remotely.
"
  exit 1
fi

HAM_IP=$(ip address show dev ham0 | awk '/inet / {print $2}' | cut -d'/' -f1)

if [[ -z "$HAM_IP" ]]; then
  zenity --error --text="Hamachi IP hostname not found. Is Hamachi running and logged in?"
  exit 1
fi

zenity --info --title="Remote Desktop Details" --text="Connect using: $HAM_IP"
EOF

  chmod +x "$HOME/.lv_connect/ShowHamachiInfo.sh"

  cat > "$DESKTOP_LAUNCHER" <<EOF
[Desktop Entry]
Name=Remote Desktop Info
Comment=Show Hamchi IP and Remote Desktop instructions
Exec=$HOME/.lv_connect/ShowHamachiInfo.sh
Icon=network-workgroup
Terminal=false
Type=Application
Categories=Network;Utility;
EOF

  chmod +x "$DESKTOP_LAUNCHER"
  gio set "$DESKTOP_LAUNCHER" metadata::trusted true || green_echo "Note: You may need to right-click the launcher and allow launching."
  green_echo "[+] Created desktop launcher at $DESKTOP_LAUNCHER"
}

# Function to check and remove a package if installed, used in new_vpn.sh
remove_if_installed_nord() {
    local pkg="$1"
    if dpkg -l | grep -q "^ii\s*$pkg"; then
        green_echo "[*] $pkg detected, removing..."
        cd $HOME/lv_linux_learn/deprecated
        ./uninstall_remote_assist.sh
    else
        green_echo "[*] $pkg not installed, skipping."
    fi
}

# Function to check and remove a package if installed, used in new_vpn.sh
remove_if_installed_hamachi() {
    local pkg="$1"
    if dpkg -l | grep -q "^ii\s*$pkg"; then
        green_echo "[*] $pkg detected, removing..."
        cd $HOME/lv_linux_learn
        ./uninstall_hamachi.sh
    else
        green_echo "[*] $pkg not installed, skipping."
    fi
}

# Function to check and remove a package if installed, used in new_vpn.sh
remove_if_installed_zerotier() {
    local pkg="$1"
    if dpkg -l | grep -q "^ii\s*$pkg"; then
        green_echo "[*] $pkg detected, removing..."
        sudo apt remove zerotier-one -y
        sudo apt purge zerotier-one -y
        green_echo "[*] Renoving zerotier-one config..."
        sudo rm -rf /var/lib/zerotier-one
        green_echo "[!] Zerotier has been removed..."
    else
        green_echo "[*] $pkg not installed, skipping."
    fi
}

remove_files(){
  green_echo "[!] Removing install and config files..."
  # Files to remove
  files=(
    "$HOME/Desktop/ShowMeshnetInfo.desktop"
    "$HOME/.lv_connect/ShowMeshnetInfo.sh"
    "$HOME/Desktop/ShowHamachiInfo.desktop"
    "$HOME/.lv_connect/ShowHamachiInfo.sh"
    "/var/lib/logmein-hamachi/h2-engine-override.cfg"
  )

  # Directories to remove
  directories=(
    "$HOME/.lv_connect"
    "/var/lib/zerotier-one"
  )

  # Remove files if they exist
  for file in "${files[@]}"; do
    if [ -f "$file" ]; then
      sudo rm "$file"
    fi
  done

  # Remove directories if they exist
  for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
      sudo rm -rf "$dir"
    fi
  done
}

remove_hamachi(){
  read -p "Press Enter to continue..." # Waits for Enter key press
  green_echo "[*] Removing logmein-hamachi..."
  sudo apt purge -y --autoremove logmein-hamachi 
  green_echo "[*] Removing config files..."
  sudo rm -rf /var/lib/logmein-hamachi
  remove_files
  green_echo "Uninstall completed!"
}

remove_nord(){
  green_echo "[!] Starting uninstaller!"
  read -p "Press Enter to continue..." # Waits for Enter key press

  green_echo "[!] Removing $USER from nordvpn group!"
  sudo gpasswd -d $USER nordvpn
  green_echo "[✓] Removed $USER from nordvpn group!"
  sleep 1

  green_echo "[!] Removing nordvpn group!"
  sudo groupdel nordvpn
  green_echo "[✓] Removed nordvpn group!"
  sleep 1

  green_echo "[!] Uninstalling nordvpn!"
  sudo apt-get remove nordvpn -y
  green_echo "[✓] Removed nordvpn!"
  sleep 1
}
