#!/bin/bash
# Usage: ./nordvpn_login.sh YOUR_TOKEN

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

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