#!/bin/bash

#functions
source includes/main.sh

# Enable 32 bit packages
green_echo "[*]Enabling 32bit packages..."
sudo dpkg --add-architecture i386

# Install wine & wind tricks
green_echo "[*]Installing wine and winetricks..."
sudo apt install wine winetricks -y

# installs the Microsoft Visual C++ 4.2 MFC runtime library (mfc42.dll)
green_echo "[*] Installing MS Visual C++ 4.2 MFC Library (mfc42.dll)"
winetricks -q mfc42

