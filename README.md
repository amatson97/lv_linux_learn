# Linux Learning Guide
> **Target Environment:** Ubuntu Desktop 24.04.3 LTS  

> **Scope:** This guide is intended for setting up a localhost environment. It does **not** cover installing or configuring publicly exposed services.

> **Prepared for:** Individuls known to me and is not be shared beyond me and that individual.
---

## 📑 Table of Contents
1. [Beginner Resources](#-beginner-resources)
2. [Installation Scripts](#️-installation-scripts)
   - [Available Bash Scripts](#available-bash-scripts)
   - [Remote Assistance Installation](#remote-assistance-installation)
     - [Disclaimer](#️-disclaimer)
   - [Remote Assistance Uninstallation](#remote-assistance-uninstallation)
3. [Linux Drive Management](#-linux-drive-management)
4. [Docker](#-docker)
   - [Official Documentation](#official-documentation)
   - [Docker Compose Commands](#docker-compose-commands)
   - [Docker Container Commands](#docker-container-commands)
   - [Docker Volume Commands](#docker-volume-commands)
   - [Docker Network Commands](#docker-network-commands)
5. [Portainer](#-portainer)
6. [Plex Media Server](#-plex-media-server)
7. [Nextcloud (Basic Install)](#-nextcloud-basic-install)
8. [Traefik (Reverse Proxy & Load Balancer)](#-traefik-reverse-proxy--load-balancer)
9. [Getting started with GitHub](#-getting-started-with-github)

---

## 📖 Beginner Resources & Tools
- [Ubuntu Desktop Install Guide](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview)
- [Useful Linux Command Reference (Hostinger)](https://www.hostinger.com/tutorials/linux-commands)
- [Linux Journey - Basic Concepts](https://linuxjourney.com/)
- [Command Lookup](https://explainshell.com/)
---

## ⚙️ Installation Scripts
This repository includes several helpful automated installation scripts.

### Available Bash Scripts
```bash
./install_remote_assist.sh
./uninstall_remote_assist.sh
./sublime_install.sh
./chrome_install.sh
./docker_install.sh
./reconnect.sh
./git_push_changes.sh
```

### ⚙️ Main functions
All the main functions across all the scripts are inside the below. You can add addtional functions in to here to call them globally.
```bash
/includes/main.php
```
You can add this top your scripts by adding this line.

```bash
source includes/main.sh
```


### Remote Assistance Installation

This uses my NordVPN meshnet to allow remote assistance to be offered. It is the only aspect of these guide that allows outside connections to your dev box.

```bash
sudo chmod +x install_remote_assist.sh
./install_remote_assist.sh
sudo reboot
./install_remote_assist.sh
```
After installation, run the desktop icon **Remote Desktop Info**.

> ⚠️ **Disclaimer:** The Remote Assistance tool is provided for convenience in localhost environments. Should you wish to remove this from your machine, run the `./uninstall_remote_assist.sh` script as described below. Do not install this functionality on anyones machine but your own.

### Remote Assistance Uninstallation
```bash
sudo chmod +x uninstall_remote_assist.sh
./uninstall_remote_assist.sh
```

### Recconect Meshnet

At times it may be reuqures to revoke ane renew the vpn login. This be dont with the below script passing the new token. (ask me for it)

```bash
sudo chmod +x reconnect.sh
./reconnect.sh <login_token>
```

---

## 💾 Linux Drive Management
- [Formatting Disks](https://phoenixnap.com/kb/linux-format-disk)
- [Mounting Disks](https://www.wikihow.com/Linux-How-to-Mount-Drive)
- [Linux Software RAID (mdadm)](https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm)
- [Disable USB Storage Quirk](https://forums.unraid.net/topic/170412-unraid-61210-how-to-permanently-add-a-usb-storage-quirk-to-disable-uas/)

---

## 🐳 Docker
Basic Docker commands for managing containers, volumes, and networks. Future updates may include `docker-compose` files for building services.

### Official Documentation
- [Docker Docs](https://docs.docker.com)

### Docker Compose Commands
```bash
docker compose up -d   # Start containers in detached mode
docker compose down    # Stop and remove containers
```

### Exmaple docker.compose.yml and .env
Example files can be found in:
```bash
docker-compose/docker-compose.yml
docker-compose/.env
```

### Docker Container Commands
```bash
sudo docker container [command]
```
Common commands include:
- `attach` – Connect to a running container
- `exec` – Execute a command in a container
- `logs` – View container logs
- `ls` – List running containers
- `restart` – Restart containers
- `run` – Create & run a new container
- `stop` – Stop containers
- `rm` – Remove containers

### Docker Volume Commands
```bash
sudo docker volume [command]
```
- `create` – Create a volume
- `inspect` – Show details
- `ls` – List volumes
- `prune` – Remove unused volumes
- `rm` – Delete volumes

### Docker Network Commands
```bash
sudo docker network [command]
```
- `create` – Create a network
- `connect` – Attach a container to a network
- `disconnect` – Remove a container from a network
- `inspect` – View details
- `ls` – List networks
- `prune` – Remove unused networks
- `rm` – Delete networks

---

## 🔧 Portainer
- [Portainer Website](https://www.portainer.io/)
- [Install Guide (Docker/Linux)](https://docs.portainer.io/start/install/server/docker/linux)

⚠️ Docker must be installed and running before installing Portainer.

---

## 🎥 Plex Media Server
You can run Plex Media Server inside Docker. Adjust the provided `docker-compose.yml` to fit your setup.

- [Plex Docker Hub (LinuxServer.io)](https://hub.docker.com/r/linuxserver/plex)

---

## ☁️ Nextcloud (Basic Install)
Instructions for running a basic Nextcloud instance (without Traefik or Cloudflare configuration):

- [Nextcloud All-in-One Install Guide](https://nextcloud.com/blog/how-to-install-the-nextcloud-all-in-one-on-linux/)

---

## 🔀 Traefik (Reverse Proxy & Load Balancer)
Recommended learning order:

1. [Introduction](https://doc.traefik.io/traefik/)
2. [Core Concepts](https://doc.traefik.io/traefik/getting-started/concepts/)
3. [FAQ](https://doc.traefik.io/traefik/getting-started/faq/)
4. [Configuration Overview](https://doc.traefik.io/traefik/getting-started/configuration-overview/)
5. [Providers Overview](https://doc.traefik.io/traefik/providers/overview/)
6. [Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
7. [Quick Start Guide](https://doc.traefik.io/traefik/getting-started/quick-start/)

---

## 🔀 Getting started with GitHub
Recommended learning order:

1. [About GitHub](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git)
2. [Start your Journey](https://docs.github.com/en/get-started/start-your-journey)
3. [Setting up git](https://docs.github.com/en/get-started/git-basics/set-up-git)
4. [Quick Start for Repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories)
5. [Managing Files](https://docs.github.com/en/repositories/working-with-files/managing-files)

---

✅ This guide is a **work-in-progress**. Contributions and improvements are welcome!

⚠️ Once we have been through all this, I will put some more together.