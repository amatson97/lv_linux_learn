#!/bin/bash

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

# Universal confirmation prompt that works in GUI (menu.py), terminal, and non-interactive environments
# Usage: confirm_action "Question text?" "Dialog Title" && do_something
# Returns: 0 if confirmed, 1 if cancelled
confirm_action() {
  local question="${1:-Are you sure you want to continue?}"
  local title="${2:-Confirm Action}"
  local default_no="${3:-yes}"  # "yes" = default to No, "no" = default to Yes
  
  # Smart confirmation: GUI dialog > interactive prompt > auto-confirm
  if command -v zenity &> /dev/null && [ -n "$DISPLAY" ]; then
    # GUI environment with zenity available (menu.py)
    if zenity --question --title="$title" --text="$question" --width=400 2>/dev/null; then
      return 0  # Yes/OK clicked
    else
      return 1  # No/Cancel clicked
    fi
  elif [ -t 0 ]; then
    # Interactive terminal (stdin is a tty)
    local prompt="$question [y/N]: "
    if [ "$default_no" = "no" ]; then
      prompt="$question [Y/n]: "
    fi
    
    read -rp "$prompt" response
    if [ "$default_no" = "no" ]; then
      # Default yes - anything except explicit 'n' is yes
      if [[ "$response" =~ ^[Nn]$ ]]; then
        return 1
      else
        return 0
      fi
    else
      # Default no - only explicit 'y' is yes
      if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
      else
        return 1
      fi
    fi
  else
    # Non-interactive environment (automated script/pipe)
    green_echo "[!] Non-interactive mode: auto-confirming after 3 seconds..."
    green_echo "[*] Press Ctrl+C to cancel..."
    sleep 3
    return 0  # Auto-confirm in non-interactive mode
  fi
}

user_in_nordvpn_group() {
  id -nG "$USER" | grep -qw "nordvpn"
}

# Prompt user for ZeroTier API token with instructions
prompt_zerotier_token() {
  local token="${ZEROTIER_API_TOKEN:-}"
  
  if [ -z "$token" ]; then
    echo
    green_echo "=== ZeroTier API Token Required ==="
    echo
    echo "To use this tool, you need a ZeroTier API token."
    echo
    echo "How to get your token:"
    echo "  1. Log in to ZeroTier Central: https://my.zerotier.com/"
    echo "  2. Click your profile icon (top-right)"
    echo "  3. Go to 'Account' → 'API Access Tokens'"
    echo "  4. Click 'Generate New Token'"
    echo "  5. Give it a name (e.g., 'LV Tools') and click 'Generate'"
    echo "  6. Copy the token (you'll only see it once!)"
    echo
    echo "Alternatively, set ZEROTIER_API_TOKEN environment variable:"
    echo "  export ZEROTIER_API_TOKEN=\"your_token_here\""
    echo
    read -sp "Enter your ZeroTier API token: " token
    echo
    
    if [ -z "$token" ]; then
      green_echo "[!] Error: No token provided"
      return 1
    fi
  fi
  
  echo "$token"
  return 0
}

# Prompt user for ZeroTier Network ID with instructions
prompt_zerotier_network() {
  local network_id="${ZEROTIER_NETWORK_ID:-}"
  
  if [ -z "$network_id" ]; then
    echo >&2
    green_echo "=== ZeroTier Network ID Required ===" >&2
    echo >&2
    echo "To use this tool, you need your ZeroTier Network ID." >&2
    echo >&2
    echo "How to find your Network ID:" >&2
    echo "  1. Log in to ZeroTier Central: https://my.zerotier.com/" >&2
    echo "  2. Select your network from the list" >&2
    echo "  3. The Network ID is at the top (16-character hex string)" >&2
    echo "     Example: 8bd5124fd60a971f" >&2
    echo >&2
    echo "Alternatively, set ZEROTIER_NETWORK_ID environment variable:" >&2
    echo "  export ZEROTIER_NETWORK_ID=\"your_network_id\"" >&2
    echo >&2
    read -p "Enter your ZeroTier Network ID: " network_id
    echo >&2
    
    if [ -z "$network_id" ]; then
      green_echo "[!] Error: No network ID provided" >&2
      return 1
    fi
    
    # Validate format (16 hex characters)
    if ! [[ "$network_id" =~ ^[0-9a-fA-F]{16}$ ]]; then
      green_echo "[!] Error: Invalid network ID format (should be 16 hex characters)" >&2
      return 1
    fi
  fi
  
  echo "$network_id"
  return 0
}

install_zerotier(){
  local network_id="${1-}"
  
  # If no parameter provided, try to get from global variable or prompt
  if [ -z "$network_id" ]; then
    if [ -n "${ZEROTIER_NETWORK:-}" ]; then
      network_id="$ZEROTIER_NETWORK"
    else
      network_id=$(prompt_zerotier_network)
    fi
  fi
  
  if [ -z "$network_id" ]; then
    green_echo "[!] Error: No network ID provided to install_zerotier function"
    return 1
  fi

  # Install dependecnies
  sudo apt install curl -y

  # Install ZeroTier
  green_echo "[*] Installing ZeroTier..."
  curl -s https://install.zerotier.com | sudo bash

  # Join network
  green_echo "[*] Joining network: $network_id"
  sleep 2

  # Join zerotier network.
  sudo zerotier-cli join "$network_id"
  green_echo "[✔] Install complete!"
}


set_permissions_zerotier_cli(){
  CURRENT_USER=$(whoami)
  SUDOERS_FILE="/etc/sudoers.d/zerotier-cli-nopasswd"
  ZEROTIER_PATH=$(which zerotier-cli)
  sudo bash -c "echo '$CURRENT_USER ALL=(ALL) NOPASSWD: $ZEROTIER_PATH' > $SUDOERS_FILE"
  sudo chmod 440 $SUDOERS_FILE
}

install_nord() {
  source ../includes/main.sh
  set -e
  
  # Prompt user for NordVPN token if not set via environment
  # Get your token at: https://my.nordaccount.com/dashboard/nordvpn/access-tokens/
  if [ -z "${NORDVPN_TOKEN:-}" ]; then
    green_echo "[*] NordVPN token required. Get yours at: https://my.nordaccount.com/dashboard/nordvpn/access-tokens/"
    read -sp "Enter your NordVPN token: " NORDVPN_TOKEN
    echo
    
    if [ -z "$NORDVPN_TOKEN" ]; then
      green_echo "[!] Error: No token provided."
      green_echo "Usage: Set NORDVPN_TOKEN environment variable or enter when prompted"
      exit 1
    fi
  fi
  
  VNC_PORT="3389"
  DESKTOP_LAUNCHER="$HOME/Desktop/ShowMeshnetInfo.desktop"

  green_echo "[*] Checking nordvpn group..."
  if ! getent group nordvpn > /dev/null; then
    green_echo "[*] Creating nordvpn group..."
    sudo groupadd nordvpn
  fi

  if ! user_in_nordvpn_group; then
    green_echo "[*] Adding user $USER to nordvpn group..."
    sudo usermod -aG nordvpn "$USER"
    green_echo
    green_echo "====================================================="
    green_echo "User $USER was added to 'nordvpn' group."
    green_echo "You must REBOOT your system now to apply this change."
    green_echo "After reboot, re-run this script to continue setup."
    green_echo "====================================================="
    read -p "Press Enter to REBOOT!..."
    sudo reboot
    exit 0
  fi

  reconnect_nord(){
    TOKEN="$1"

    if [ -z "$TOKEN" ]; then
        green_echo "[!] Error no token provided."
        green_echo "Usage: $0 <login_token>"
        exit 1
    fi

    # Login to NordVPN using the provided token
    green_echo "[*] Logging in to Meshnet..."
    nordvpn login --token "$TOKEN"

    # Ensure tray icon and notificatiosn disbaled
    nordvpn set notify off
    nordvpn set tray off
    nordvpn set autoconnect off

    # Check login status
    nordvpn account
  }

  green_echo "[*] User $USER is in 'nordvpn' group. Proceeding with installation..."

  green_echo "[*] Installing NordVPN..."
  sh <(wget -qO - https://downloads.nordcdn.com/apps/linux/install.sh) -p -y nordvpn-gui
  sudo apt install -y nordvpn
  nordvpn set notify off
  nordvpn set tray off

  green_echo "[*] Logging into NordVPN with token..."
  if [[ -z "$NORDVPN_TOKEN" ]]; then
    green_echo "[!] ERROR: NORDVPN_TOKEN is empty. Please set your token in the script."
    exit 1
  fi
  nordvpn login --token "$NORDVPN_TOKEN"

  green_echo "[*] Enabling NordVPN Meshnet..."
  nordvpn set meshnet on

  create_meshnet_info_desktop_icon
  nordvpn set autoconnect off
  green_echo "[✓] Setup complete! Use the desktop icon 'Show NordVPN Meshnet Info' on your desktop."
  green_echo "[!] DISCLAIMER: Your can remove this from your system running ./uninstall_remote_assist.sh"
  green_echo "    Remember to enable GNOME Remote Desktop (Settings → System → Remote Desktop)."
}

create_meshnet_info_desktop_icon() {
  mkdir -p "$HOME/.lv_connect"
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

create_zerotier_info_desktop_icon() {
  DESKTOP_LAUNCHER="$HOME/Desktop/ShowZerotierInfo.desktop"
  mkdir $HOME/.lv_connect
  cat > "$HOME/.lv_connect/ShowZerotierInfo.sh" <<'EOF'
#!/bin/bash

ZT_IP="$(sudo zerotier-cli listnetworks | awk '{ for(i=1;i<=NF;i++) if ($i ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+$/) {split($i,a,"/"); print a[1]; exit} }')"

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

After enabling, use the hostname:$ZT_IP to connect remotely.
"
  exit 1
fi

ZT_IP="$(sudo zerotier-cli listnetworks | awk '{ for(i=1;i<=NF;i++) if ($i ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+$/) {split($i,a,"/"); print a[1]; exit} }')"

if [[ -z "$ZT_IP" ]]; then
  zenity --error --text="Zerotier IP hostname not found. Has Adam authorised your login?"
  exit 1
fi

zenity --info --title="Remote Desktop Details" --text="Connect using: $ZT_IP"
EOF

  chmod +x "$HOME/.lv_connect/ShowZerotierInfo.sh"

  cat > "$DESKTOP_LAUNCHER" <<EOF
[Desktop Entry]
Name=Remote Desktop Info
Comment=Show Zerotier IP and Remote Desktop instructions
Exec=$HOME/.lv_connect/ShowZerotierInfo.sh
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
        green_echo "Leaving ZeroTier networks..."
        # Leave all networks (zerotier-cli listnetworks shows joined networks)
        sudo zerotier-cli listnetworks | tail -n +2 | awk '{print $3}' | xargs -r -I {} sudo zerotier-cli leave {}
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
    "$HOME/Desktop/ShowZerotierInfo.desktop"
    "$HOME/.lv_connect/ShowZerotierInfo.sh"
    "/var/lib/logmein-hamachi/h2-engine-override.cfg"
    "/etc/sudoers.d/zerotier-cli-nopasswd"
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

show_menu() {
  echo
  printf "%-4s %-20s  %s\n" "No." "Script Name" "Description"
  printf "%-4s %-20s  %s\n" "---" "-----------" "-----------"
  for i in "${!SCRIPTS[@]}"; do
    script_name=$(basename "${SCRIPTS[$i]}")
    printf "[%-4s %-20s  %s\n" "$((i+1))]" "$script_name" "${DESCRIPTIONS[$i]}"
  done
  echo "[0]   Exit"
  echo
}

# Uninstaller helper functions
confirm_uninstall() {
  local package_name="$1"
  confirm_action "Are you sure you want to uninstall $package_name?" "Confirm Uninstall"
}

check_installed() {
  local package="$1"
  if command -v "$package" &> /dev/null; then
    return 0
  elif dpkg -l | grep -q "^ii.*$package"; then
    return 0
  else
    return 1
  fi
}
