#!/bin/bash
# Uninstall Docker and Docker Compose
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

main() {
    green_echo "[*] Uninstalling Docker and Docker Compose..."
    
    if ! command -v docker &> /dev/null; then
        green_echo "[!] Docker is not installed."
        return 0
    fi
    
    # Warning about data loss
    echo ""
    echo "WARNING: This will remove Docker and all containers, images, volumes, and networks!"
    read -rp "Are you sure you want to continue? [y/N]: " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        green_echo "[*] Uninstall cancelled."
        return 0
    fi
    
    # Stop all containers
    green_echo "[*] Stopping all Docker containers..."
    docker stop $(docker ps -aq) 2>/dev/null || true
    
    # Remove all containers
    green_echo "[*] Removing all Docker containers..."
    docker rm $(docker ps -aq) 2>/dev/null || true
    
    # Remove all images
    green_echo "[*] Removing all Docker images..."
    docker rmi $(docker images -q) 2>/dev/null || true
    
    # Stop Docker service
    green_echo "[*] Stopping Docker service..."
    sudo systemctl stop docker 2>/dev/null || true
    sudo systemctl disable docker 2>/dev/null || true
    
    # Remove Docker packages
    green_echo "[*] Removing Docker packages..."
    sudo apt remove --purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true
    sudo apt autoremove -y
    
    # Remove Docker repository
    green_echo "[*] Removing Docker repository..."
    sudo rm -f /etc/apt/sources.list.d/docker.list
    sudo rm -f /etc/apt/keyrings/docker.gpg
    
    # Remove Docker data
    green_echo "[*] Removing Docker data directories..."
    sudo rm -rf /var/lib/docker
    sudo rm -rf /var/lib/containerd
    sudo rm -rf /etc/docker
    sudo rm -rf ~/.docker
    
    # Remove user from docker group
    green_echo "[*] Removing user from docker group..."
    sudo deluser "$USER" docker 2>/dev/null || true
    
    green_echo "[+] Docker has been uninstalled successfully!"
    green_echo "[!] You may need to reboot to fully remove group membership."
}

main "$@"
