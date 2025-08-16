#!/bin/bash
#Install the GPG key:
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/sublimehq-archive.gpg > /dev/null

#Ensure apt is set up to work with https sources:
sudo apt-get install apt-transport-https

#Select the channel to use:
#Stable
echo "deb https://download.sublimetext.com/ apt/stable/" | sudo tee /etc/apt/sources.list.d/sublime-text.list

#Dev
#echo "deb https://download.sublimetext.com/ apt/dev/" | sudo tee /etc/apt/sources.list.d/sublime-text.list
#Update apt sources and install Sublime Merge

sudo apt-get update
sudo apt-get install sublime-merge