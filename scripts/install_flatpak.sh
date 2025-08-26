#!/bin/bash
# Install flatpak, a useful software repository. Has its own software store as well.

sudo apt install flatpak
sudo apt install gnome-software-plugin-flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
