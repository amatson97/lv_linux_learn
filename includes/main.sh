#!/bin/bash

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

user_in_nordvpn_group() {
  id -nG "$USER" | grep -qw "nordvpn"
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