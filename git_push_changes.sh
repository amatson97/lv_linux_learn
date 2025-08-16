#!/bin/bash
# Script to commit changes to github

green_echo() {
  # Use ANSI-C quoting to interpret \e, no recursion
  echo -e $'\e[32m'"$1"$'\e[0m'
}

green_echo "[*] Stagging changes..."
sudo git add .
green_echo "[*] Commiting chnages..."
sudo git commit
sleep 1

green_echo "[!] About to push changes..."
read -p "Press Enter to continue..." # Waits for Enter key press
git push