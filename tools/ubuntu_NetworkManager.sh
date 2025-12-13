#!/bin/bash
# Description: Migrate Ubuntu from netplan to NetworkManager for network configuration

echo "Migrating netplan to NetworkManager..."

# Step 1: Install NetworkManager if not present
if ! dpkg -l | grep -qw network-manager; then
    sudo apt update
    sudo apt install -y network-manager
fi

# Step 2: Backup all existing netplan configuration files
sudo mkdir -p /etc/netplan/backup
sudo cp /etc/netplan/*.yaml /etc/netplan/backup/

# Step 3: Overwrite with basic NetworkManager renderer config
sudo bash -c 'cat > /etc/netplan/01-netcfg.yaml <<EOF
network:
  version: 2
  renderer: NetworkManager
EOF
'

# Step 4: Apply and enable NetworkManager
sudo netplan generate
sudo netplan apply
sudo systemctl enable NetworkManager.service
sudo systemctl restart NetworkManager.service

echo "Migration complete. Check your interfaces in NetworkManager."