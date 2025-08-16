#!/bin/bash
#Install chrome

# Download .deb file
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Install
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Clean up
rm google-chrome-stable_current_amd64.deb