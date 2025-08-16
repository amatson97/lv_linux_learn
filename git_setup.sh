#!/bin/bash
# Script to set up ubuntu 22.04 and above with git and gh.
# This till install the the required packages, then guide you through authenticating.
# HTTPS is the best if running this on Ubuntu Desktop.

# Includes
source includes/main.sh

# Install Git if not installed
if ! command -v git &> /dev/null; then
    green_echo "Git not found. Installing Git..."
    sudo apt update
    sudo apt install -y git
else
    green_echo "Git is already installed."
fi

# Install GitHub CLI if not installed
if ! command -v gh &> /dev/null; then
    green_echo "GitHub CLI (gh) not found. Installing GitHub CLI from Ubuntu repos..."
    sudo apt update
    sudo apt install -y gh
else
    green_echo "GitHub CLI is already installed."
fi

# Configure Git user name and email
read -p "Enter your GitHub name: " name
git config --global user.name "$name"

read -p "Enter your GitHub email: " email
git config --global user.email "$email"

echo "Git user name and email configured."

# Authenticate GitHub CLI with GitHub via HTTPS (interactive login)
green_echo "Authenticating GitHub CLI..."
green_echo "Select HTTPS for Ubuntu Desktop..."
gh auth login --hostname github.com --web

green_echo "Setup complete! You can now use Git commands and GitHub CLI with HTTPS authentication."