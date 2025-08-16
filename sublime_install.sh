#!/bin/bash
#Install Sublime https://www.sublimetext.com/

#Install CPG key
wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | sudo tee /etc/apt/keyrings/sublimehq-pub.asc > /dev/null

#Select stable channel
echo -e 'Types: deb\nURIs: https://download.sublimetext.com/\nSuites: apt/stable/\nSigned-By: /etc/apt/keyrings/sublimehq-pub.asc' | sudo tee /etc/apt/sources.list.d/sublime-text.sources


#Ensure apt is set up to work with https sources:
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install sublime-text sublime-merge -y