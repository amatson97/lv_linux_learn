#!/bin/bash
#Install Sublime https://www.sublimetext.com/

# Includes
source includes/main.sh

green_echo "[*] Install CPG key..."
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo tee /etc/apt/keyrings/sublimehq-pub.asc > /dev/null

green_echo "[*] Selecting stable channel..."
echo -e 'Types: deb\nURIs: https://download.sublimetext.com/\nSuites: apt/stable/\nSigned-By: /etc/apt/keyrings/sublimehq-pub.asc' | sudo tee /etc/apt/sources.list.d/sublime-text.sources

green_echo "[*] Installing prerequisites..."
sudo apt-get install apt-transport-https

green_echo "[*] Installing sublime-test and sublime_merge"
sudo apt-get update
sudo apt-get install sublime-text sublime-merge -y