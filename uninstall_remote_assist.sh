#!/bin/bash
sudo gpasswd -d $USER nordvpn
sudo groupdel nordvpn
sudo apt-get remove nordvpn
rm $HOME/Desktop/ShowMeshnetInfo.desktop
rm $HOME/.lv_connect/ShowMeshnetInfo.sh