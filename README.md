# Linux Learning Guide

![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04.3%20LTS-orange)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

> **Target Environment:** Ubuntu Desktop 24.04.3 LTS  
> **Scope:** This guide is intended for setting up a localhost environment. It does **not** cover installing or configuring publicly exposed services.  
> **Prepared for:** Individuals known to me and is not to be shared beyond me and that individual.

---

## 🚀 Quick Navigation
- 🏁 [New User Start Here](#-quick-start)
- 📋 [Prerequisites](#-prerequisites)
- ⚙️ [Installation Scripts](#%EF%B8%8F-installation-scripts)
- 🆘 [Troubleshooting](#%EF%B8%8F-essential-linux-troubleshooting)
- 💬 [Community Support](#-community-support)

---

## 📑 Table of Contents
1. [Beginner Resources & Tools](#-beginner-resources--tools)
2. [Package Manager (apt)](#-package-manager-apt)
3. [Installation Scripts](#%EF%B8%8F-installation-scripts)
4. [Linux Drive Management](#-linux-drive-management)
5. [Docker](#-docker)
6. [Portainer](#-portainer)
7. [Plex Media Server](#-plex-media-server)
8. [Nextcloud (Basic Install)](#%EF%B8%8F-nextcloud-basic-install)
9. [Traefik (Reverse Proxy & Load Balancer)](#-traefik-reverse-proxy--load-balancer)
10. [Getting Started with GitHub](#-getting-started-with-github)
11. [Essential Linux Troubleshooting](#%EF%B8%8F-essential-linux-troubleshooting)
12. [AI Integration Tools](#-ai-integration-tools)
13. [ZeroTier Network Tools](#-zerotier-network-tools)
14. [Utility Tools](#-utility-tools)

---

## 📖 Beginner Resources & Tools
- [VMware Workstation Pro FREE (Sign up required)](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true)
- [Balena Etcher USB Imager](https://etcher.balena.io)
- [Ubuntu Desktop Install Guide](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview)
- [Useful Linux Command Reference (Hostinger)](https://www.hostinger.com/tutorials/linux-commands)
- [Linux Journey - Basic Concepts](https://linuxjourney.com/)
- [Command Lookup](https://explainshell.com/)
- [Chmod Calculator](https://chmod-calculator.com/)

### VMWare Workstation Pro FREE

Once logged in go to https://support.broadcom.com/group/ecx/free-downloads then search for "VMware Workstation Pro".

![VMware Workstation Pro FREE](images/broadcomm.png "VMWare Workstation Pro FREE")

---

## 🏁 Quick Start

### New to Linux? Start here:
1. **Clone this repository:**
```bash
sudo apt update
sudo apt install -y gh
git config --global user.name "GIT_HUB_USERNAME"
git config --global user.email "GIT_HUB_EMAIL"
gh auth login --hostname github.com --web
gh repo clone amatson97/lv_linux_learn
cd lv_linux_learn
```

2. **Make scripts executable:**
```bash
chmod +x scripts/*.sh includes/*.sh tools/*.sh zerotier_tools/*.sh ai_fun/*.sh *.sh
```

3. **Run the installation menu:**
```bash
# Recommended: Auto-launcher (detects GUI vs CLI)
./launcher.sh

# Or run specific interface:
./menu.py       # GUI version (requires GTK)
./menu.sh       # CLI version (works everywhere)

# Or run the uninstaller menu
./uninstall_menu.sh
```

4. **Follow the [Beginner Resources](#-beginner-resources--tools)** section for foundational learning.

---

## 📋 Prerequisites

### System Requirements
- **OS:** Ubuntu Desktop 24.04.3 LTS (recommended)
- **RAM:** Minimum 4GB, 8GB+ recommended for Docker containers
- **Storage:** 20GB+ free space for tools and containers
- **Network:** Internet connection for package downloads

### Required Permissions
- **Sudo access:** Required for package installation and system configuration
- **User account:** Must be in the `docker` group (installation scripts will configure this automatically)

### Recommended Dependencies
The following tools enhance functionality but are optional:
- **fzf** — Fuzzy finder for interactive menus (used by some AI tools)
- **bat** — Colorized file viewer (enhances output rendering)
- **jq** — JSON processor (required for AI integration tools)

Install recommended dependencies:
```bash
sudo apt update && sudo apt install -y fzf bat jq
```

## Repository Structure

```
lv_linux_learn/
├── ai_fun/                            # AI integration tools and desktop applications
│   ├── perplex_cli_v1.1.sh           # Enhanced Perplexity CLI with context, streaming, Mermaid
│   ├── perplex.sh                     # Legacy command-line Perplexity AI client
│   └── python/                        # Python-based AI desktop applications
│       ├── assets/                    # Desktop integration files (icons, .desktop)
│       ├── generated_md_files/        # AI-generated documentation examples
│       └── perplexity_desktop_*.py    # Desktop GUI versions (v1.0-v1.4)
├── bash_exercises/                    # Basic bash scripting examples and exercises
│   ├── count_lines.sh                 # Text processing examples
│   ├── simple_calculator.sh           # Basic arithmetic operations
│   └── *.txt                          # Sample data files for exercises
├── deprecated/                        # Legacy VPN tools (Hamachi-based)
│   └── *.sh                           # Old installation/removal scripts
├── docker-compose/                    # Docker configuration examples
│   ├── docker-compose.yml             # Multi-service container setup
│   └── wordpress_install.sh           # WordPress deployment script
├── images/                            # Documentation screenshots and assets
│   ├── remote_settings.png            # Remote desktop configuration
│   └── zt_notifications.png           # ZeroTier notification examples
├── includes/                          # Shared functions and utilities
│   └── main.sh                        # Global function library (green_echo, etc.)
├── scripts/                           # Main installation and setup scripts
│   ├── docker_install.sh              # Docker engine + CLI + plugins installation
│   ├── chrome_install.sh              # Google Chrome installation
│   ├── new_vpn.sh                     # ZeroTier VPN setup + network join
│   ├── remove_all_vpn.sh              # Remove all VPN clients (ZeroTier, NordVPN, Hamachi)
│   ├── git_setup.sh                   # Git + GitHub CLI configuration
│   ├── git_pull.sh                    # Pull latest changes from repository
│   ├── git_push_changes.sh            # Stage, commit, and push changes
│   ├── install_flatpak.sh             # Flatpak + Flathub repository setup
│   ├── install_wine.sh                # Wine + Winetricks + mfc42.dll installation
│   ├── nextcloud_client.sh            # Nextcloud Desktop client via Flatpak
│   └── sublime_install.sh             # Sublime Text + Sublime Merge installation
├── tools/                             # File management and conversion utilities
│   ├── 7z_extractor*.sh               # Archive extraction with RAM disk support
│   ├── extract-xiso/                  # Xbox ISO extraction tool (compiled)
│   ├── flac_to_mp3.sh                 # Audio format conversion
│   ├── convert_*.sh                   # Various file format converters
│   └── check_power_on*.sh             # Check power-on hours of disks in your system
├── uninstallers/                      # ⚠️ Removal scripts for installed tools
│   ├── uninstall_zerotier.sh          # Remove ZeroTier VPN
│   ├── uninstall_nordvpn.sh           # Remove NordVPN
│   ├── uninstall_docker.sh            # Remove Docker (with data warning)
│   ├── uninstall_chrome.sh            # Remove Google Chrome
│   ├── uninstall_sublime.sh           # Remove Sublime Text
│   ├── uninstall_flatpak.sh           # Remove Flatpak
│   ├── uninstall_wine.sh              # Remove Wine
│   ├── uninstall_nextcloud.sh         # Remove Nextcloud Client
│   ├── uninstall_all_vpn.sh           # Remove all VPN tools at once
│   ├── clean_desktop_launchers.sh     # Clean desktop icons only
│   └── README.md                      # Uninstaller documentation
├── zerotier_tools/                    # VPN network management and monitoring
│   ├── get_ip.sh                      # Network member IP discovery
│   ├── html_ip.sh                     # Generate network status reports
│   └── zt_notifications.sh            # Desktop notifications for network changes
├── .github/
│   └── copilot-instructions.md        # AI coding assistant guidelines
├── launcher.sh                        # 🚀 Auto-launcher (detects GUI vs CLI)
├── menu.py                            # Python GTK GUI menu (desktop version)
├── menu.sh                            # Bash CLI menu (terminal version)
├── uninstall_menu.sh                  # ⚠️ Interactive uninstaller menu
└── README.md                          # This documentation file
```

### 🚀 Menu Interfaces

This repository provides **three ways** to run the setup tool:

**1. Auto-Launcher (Recommended)**
```bash
./launcher.sh
```
Automatically detects your environment and launches:
- **GUI version** (`menu.py`) if running on desktop with GTK installed
- **CLI version** (`menu.sh`) if running over SSH or without GUI

**2. GUI Menu (Desktop)**
```bash
./menu.py
```
Features:
- 📦 Install, 🔧 Tools, 📚 Exercises, ⚠️ Uninstall, ℹ️ About tabs
- Embedded VTE terminal for interactive script execution
- Syntax highlighting with descriptions
- Search/filter functionality
- Right-click context menu (copy/paste)

Requirements: `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-vte-2.91`

**3. CLI Menu (Terminal)**
```bash
./menu.sh
```
Features:
- Text-based interactive menu
- Works over SSH and headless systems
- No GUI dependencies required
- Identical functionality to GUI version

---

## 📦 Package Manager (apt)

The **apt** package manager is the primary tool for installing, updating, and managing software on Ubuntu and most Debian-based Linux systems. Understanding how to use apt will help you maintain your system, install new tools, and keep everything up-to-date.

### Common apt Commands

- **Update package lists**
```bash
sudo apt update
```
Refreshes your local index of available software packages.

- **Upgrade installed packages**
```bash
sudo apt upgrade
```
Installs the latest versions of all packages currently installed.

- **Install a package**
```bash
sudo apt install <package-name>
```
Installs a new package (example: `sudo apt install htop`).

- **Remove a package**
```bash
sudo apt remove <package-name>
```
Removes a package but leaves its configuration files.

- **Purge a package**
```bash
sudo apt purge <package-name>
```
Removes a package and its configuration files.

- **Search for packages**
```bash
apt search <keyword>
```
Lists available packages matching your keyword.

- **Show package details**
```bash
apt show <package-name>
```
Displays detailed information about a package.

- **List upgradable packages**
```bash
apt list --upgradable
```

- **Clean the apt cache**
```bash
sudo apt clean
```
Frees up space used to store packages after installation.

### Useful Tips

- Always run `sudo apt update` before installing new software to ensure you have the latest repositories.
- Use `apt list --installed` to see all installed packages.
- You can combine `update` and `upgrade`:
```bash
sudo apt update && sudo apt upgrade
```
- For advanced management tasks, see the [Apt User Guide](https://help.ubuntu.com/community/AptGet/Howto).

---

## ⚙️ Installation Scripts

This repository includes automated installation scripts for common tools and services. All scripts follow consistent patterns:
- **Idempotent:** Safe to run multiple times (checks if already installed)
- **Error handling:** Uses `set -euo pipefail` for robust failure detection
- **Status messages:** Clear feedback using `green_echo` helper function
- **Repo-aware:** Sources shared functions from `includes/main.sh`

### Interactive Menu

The installation menu provides a user-friendly interface to run all scripts:

```bash
# Navigate to the repository directory
cd ~/lv_linux_learn

# Run the interactive menu
./menu.sh

# Or run the Python GUI version (beta)
./menu.py
```

**Menu features:**
- Color-coded status indicators (ready/missing/not executable)
- Descriptive explanations for each script
- Automatic error handling and status reporting
- Visual separation of script output

### Available Installation Scripts

| Script | Description | Prerequisites |
|--------|-------------|---------------|
| `chrome_install.sh` | Google Chrome web browser | None |
| `docker_install.sh` | Docker engine + CLI + plugins | None |
| `git_setup.sh` | Git + GitHub CLI with authentication | None |
| `install_flatpak.sh` | Flatpak + Flathub repository | None |
| `install_wine.sh` | Wine + Winetricks + mfc42.dll | None |
| `nextcloud_client.sh` | Nextcloud Desktop client | Flatpak |
| `sublime_install.sh` | Sublime Text + Sublime Merge | None |
| `new_vpn.sh` | ZeroTier VPN + network join | None |
| `git_pull.sh` | Pull latest repository changes | Git |
| `git_push_changes.sh` | Stage, commit, and push changes | Git |

### Uninstaller System

Safe removal of installed tools with cleanup:

```bash
# Interactive uninstaller menu
./uninstall_menu.sh

# Or run individual uninstallers directly
./uninstallers/uninstall_docker.sh
./uninstallers/uninstall_zerotier.sh
./uninstallers/uninstall_chrome.sh
```

**Available uninstallers:**
- `uninstall_zerotier.sh` - Remove ZeroTier VPN (leaves networks first)
- `uninstall_nordvpn.sh` - Remove NordVPN (disconnects & removes group)
- `uninstall_docker.sh` - Remove Docker (warns about data loss)
- `uninstall_chrome.sh` - Remove Google Chrome (optional user data removal)
- `uninstall_sublime.sh` - Remove Sublime Text (optional config removal)
- `uninstall_flatpak.sh` - Remove Flatpak (optional app removal)
- `uninstall_wine.sh` - Remove Wine (optional prefix removal)
- `uninstall_nextcloud.sh` - Remove Nextcloud Client (optional config removal)
- `remove_all_vpn.sh` - [Legacy] Remove all VPN clients (older implementation)
- `uninstall_all_vpn.sh` - Remove all VPN tools at once (recommended)
- `clean_desktop_launchers.sh` - Remove desktop icons only

**What gets removed:**
- Installed packages (with `--purge` flag)
- Repository configurations and GPG keys
- System service configurations
- User group memberships
- Desktop launchers and helper scripts
- Optionally: user data and configurations (with confirmation)

See [uninstallers/README.md](uninstallers/README.md) for detailed documentation.

### Git Workflow Scripts

Simplified Git operations for repository management:

```bash
# Pull latest changes from GitHub
./tools/git_pull.sh

# Commit and push all changes
./tools/git_push_changes.sh
```

**Note:** `git_push_changes.sh` will:
1. Check Git configuration (runs `git_setup.sh` if needed)
2. Show current changes with `git status`
3. Stage all changes with `git add .`
4. Open your editor for commit message
5. Prompt for confirmation before pushing

### Shared Functions Library

All scripts source the shared function library for consistent behavior:

```bash
# Location
includes/main.sh

# Usage in your scripts
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
source "$repo_root/includes/main.sh"

# Available functions
green_echo "Status message"  # Green colored output for success/info
```

### Remote Assistance Installation

⚠️ **Security Warning**: VPN scripts modify system network configuration. Ensure you have local access before running remote assistance tools.

To add your VM to the Linux learning network (facilitated by ZeroTier VPN):

```bash
# Run the VPN setup script (also available in menu)
./scripts/new_vpn.sh
```

**What this script does:**
1. Installs ZeroTier One client
2. Joins the Linux Learn Network (network ID embedded)
3. Removes conflicting VPN clients (NordVPN, Hamachi)

After installation, enable remote desktop in: **Settings > System > Remote Desktop**

![Remote Settings Screenshot](images/remote_settings.png "Remote Settings Screenshot")

### Uninstall All VPNs

Remove all VPN technologies from your machine:

```bash
./scripts/remove_all_vpn.sh
```

This removes:
- ZeroTier One
- NordVPN
- LogMeIn Hamachi

You can then disable remote desktop features in system settings.

---

## 💾 Linux Drive Management
- [Formatting Disks](https://phoenixnap.com/kb/linux-format-disk)
- [Mounting Disks](https://www.wikihow.com/Linux-How-to-Mount-Drive)
- [Linux Software RAID (mdadm)](https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm)
- [Disable USB Storage Quirk](https://forums.unraid.net/topic/170412-unraid-61210-how-to-permanently-add-a-usb-storage-quirk-to-disable-uas/)

---

## 🐳 Docker

Docker enables containerized application deployment. The repository includes installation scripts and docker-compose examples.

⚠️ **Security Best Practices:**
- Never run containers as root unless absolutely necessary
- Always review Docker images from trusted sources
- Keep your Docker installation updated
- Use specific version tags instead of `latest` in production

### Installation

```bash
# Run from the interactive menu, or directly:
./scripts/docker_install.sh
```

**What the script installs:**
- Docker Engine (CE)
- Docker CLI
- containerd
- Docker Buildx plugin
- Docker Compose plugin

**Post-installation:**
- Adds your user to the `docker` group (log out/in required)
- Enables Docker service at boot
- Runs `hello-world` container to verify installation

### Official Documentation
- [Docker Docs](https://docs.docker.com)

### Docker Compose Commands

```bash
# Navigate to directory with docker-compose.yml first
cd docker-compose/

# Start containers in detached mode
docker compose up -d

# Stop and remove containers
docker compose down

# View running services
docker compose ps

# View logs
docker compose logs -f
```

### Example docker-compose.yml and .env

Example files can be found in:
```
docker-compose/docker-compose.yml
docker-compose/.env
```

### Docker Container Commands

```bash
docker container [command]
```

Common commands include:
- `attach` – Connect to a running container
- `exec` – Execute a command in a container (e.g., `docker exec -it container_name bash`)
- `logs` – View container logs
- `ls` – List running containers (`docker ps` also works)
- `restart` – Restart containers
- `run` – Create & run a new container
- `stop` – Stop containers
- `rm` – Remove containers

### Docker Volume Commands

```bash
docker volume [command]
```

- `create` – Create a volume
- `inspect` – Show details
- `ls` – List volumes
- `prune` – Remove unused volumes
- `rm` – Delete volumes

### Docker Network Commands

```bash
docker network [command]
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

⚠️ **Prerequisites**: Docker must be installed and running before installing Portainer.

---

## 🎥 Plex Media Server

You can run Plex Media Server inside Docker. Adjust the provided `docker-compose/docker-compose.yml` to fit your setup.

- [Plex Docker Hub (LinuxServer.io)](https://hub.docker.com/r/linuxserver/plex)

**Configuration Notes:**
- Ensure proper volume mappings for your media directories
- Set appropriate `PUID` and `PGID` for file permissions
- Consider using hardware transcoding if your system supports it

---

## ☁️ Nextcloud (Basic Install)

Install Nextcloud Desktop Client via Flatpak:

```bash
# Run from the interactive menu, or directly:
./scripts/nextcloud_client.sh
```

For server installation (without Traefik or Cloudflare configuration):
- [Nextcloud All-in-One Install Guide](https://nextcloud.com/blog/how-to-install-the-nextcloud-all-in-one-on-linux/)

**Security Considerations:**
- Change default passwords immediately
- Enable two-factor authentication
- Regular security updates are essential

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

## 📚 Getting Started with GitHub

Recommended learning order:

1. [About GitHub](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git)
2. [Start Your Journey](https://docs.github.com/en/get-started/start-your-journey)
3. [Setting up Git](https://docs.github.com/en/get-started/git-basics/set-up-git)
4. [Quick Start for Repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories)
5. [Managing Files](https://docs.github.com/en/repositories/working-with-files/managing-files)

### Repository Setup

```bash
# Install Git and GitHub CLI (automated)
./scripts/git_setup.sh

# This script will:
# 1. Install git and gh packages
# 2. Configure git user.name and user.email (if not set)
# 3. Guide you through 'gh auth login' for GitHub authentication
```

---

## 🛠️ Essential Linux Troubleshooting

Troubleshooting is an essential skill for any Linux user. This section covers common techniques and tools to help diagnose and fix issues effectively.

### Common Command-Line Pitfalls

- **Misspelled commands** or options — use `command --help` to verify syntax
- **Permissions errors** — check file ownership and permissions with `ls -l`
- **Incorrect environment variables** — verify with `echo $VARIABLE_NAME`
- **Path issues** — confirm executable locations using `which <command>`

### Reading and Understanding Log Files

System logs provide valuable insights into system behavior and errors:

```bash
# View system logs
sudo less /var/log/syslog

# Use journalctl for systemd-based logging
sudo journalctl -xe

# Check specific service logs (e.g., SSH)
sudo journalctl -u ssh

# Follow logs in real-time
sudo journalctl -f
```

### System Resource Monitoring Tools

Monitor system health and resource usage:

- `top` — Interactive process viewer
- `htop` — Enhanced version of top (install with `sudo apt install htop`)
- `free -h` — Display memory usage
- `df -h` — Show disk space usage
- `du -sh <directory>` — Show size of a directory
- `ps aux` — List all running processes
- `kill <pid>` or `kill -9 <pid>` — Terminate a process by PID
- `lsof` — List open files (useful for finding which process is using a file)

### Network Troubleshooting

Diagnose connectivity and networking issues:

```bash
# Test network reachability
ping <hostname/ip>

# Trace the route packets take
traceroute <hostname>

# Show listening ports and connections
netstat -tuln
ss -tuln

# Check if a port is open
nc -zv <host> <port>

# Display IP addresses and interfaces
ip addr
ifconfig  # deprecated but still useful

# DNS lookup testing
nslookup <domain>
```

### Additional Troubleshooting Tips

```bash
# View kernel messages (useful for hardware-related issues)
dmesg | less

# Restart services to apply changes or clear stuck states
sudo systemctl restart <service-name>
sudo systemctl status <service-name>

# Check disk usage when systems become slow
sudo du -h --max-depth=1 / | sort -hr
```

**When in doubt:** Search error messages online or check Linux community forums (see [Community Support](#-community-support))

---

## 🤖 AI Integration Tools

The repository includes Perplexity AI integration tools for command-line and desktop use.

### Enhanced Perplexity CLI (v1.1) BETA

**Features:**
- Multi-turn conversations with persistent context
- Streaming responses for faster feedback
- Multiple output formats (Plain, Markdown, JSON, Shell, Auto)
- Automatic Mermaid diagram support for workflows/architecture
- Client-side syntax highlighting (bat/pygmentize)
- Save responses to Markdown files

**Installation:**

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Make script executable
chmod +x perplex_cli_v1.1.sh

# Run with API key (or set PERPLEXITY_API_KEY env var)
./perplex_cli_v1.1.sh <Your_API_Key>

# API key will be saved to ~/.perplexity_api_key on first run
```

**Usage:**

```bash
# Interactive mode (default)
./perplex_cli_v1.1.sh

# Pipe mode for automation
echo "Explain Docker networking" | ./perplex_cli_v1.1.sh --cli
```

**Interactive Commands:**

```
:help                 Show all commands
:exit                 Quit
:format <type>        Set format (Plain|Markdown|JSON|Shell|Auto)
:render <on|off>      Toggle client-side rendering
:stream <on|off>      Toggle streaming mode
:context <on|off>     Enable/disable conversation history
:history              View saved conversation context
:save <file>          Save last response to Markdown file
:clear                Clear the terminal
```

**Example session:**

```
perplexity> :format Markdown
Format set: Markdown

perplexity> :context on
Context ON

perplexity> Explain the OSI model with a diagram
Enter multi-line input; end with a line containing only EOF
EOF

[Response with Mermaid diagram will be displayed]

perplexity> :save osi_model.md
Saved to osi_model.md
```

**Requirements:**
- Perplexity API key (get from https://www.perplexity.ai/)
- **Recommended:** `jq`, `bat`, `fzf` for enhanced functionality
  ```bash
  sudo apt install -y jq bat fzf
  ```

### Legacy Perplexity Script

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Run with API key
./perplex.sh <Perplexity_API_Key>
```

**How it works:**
1. Enter your query when prompted
2. Type `EOF` on a new line to submit
3. Response rendered in markdown format
4. Option to export to `.md` file

### Python Desktop Applications

Desktop GUI versions are available in `ai_fun/python/` (v1.0-v1.4).

---

## 🌐 ZeroTier Network Tools

The `zerotier_tools` directory contains utilities for managing and monitoring ZeroTier VPN networks.

### Available Scripts

```bash
# Get IP addresses of network members
./get_ip.sh <API_TOKEN> <NETWORK_ID>

# Generate HTML report of network status
./html_ip.sh <API_TOKEN> <NETWORK_ID>

# Desktop notifications for network changes
./zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

### Automated Monitoring Setup

Configure desktop notifications for network member status changes:

```bash
# Edit crontab
crontab -e

# Add this line (replace placeholders with actual values)
*/5 * * * * DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/<USER>/lv_linux_learn/zerotier_tools/zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

**What it does:**
- Checks every 5 minutes for network member status changes
- Issues desktop notifications when nodes come online/offline
- Shows member names and IP addresses

![ZeroTier Desktop Notifications](images/zt_notifications.png "ZeroTier Desktop Notifications")

**Note:** Contact the repository administrator for `<API_TOKEN>` and `<NETWORK_ID>` values.

---

## 🔧 Utility Tools

The `tools` directory contains various utility scripts for file management and system optimization.

**Common features:**
- Extract 7z and zip files automatically
- Remove source archives after extraction
- Utilize RAM disk for increased performance during operations
- Batch processing capabilities

### Usage

```bash
# Navigate to tools directory
cd tools/

# Make scripts executable
chmod +x *.sh

# Run specific utility (check script comments for usage)
./script_name.sh
```

**Available tools:**
- `7z_extractor*.sh` — Archive extraction with RAM disk support
- `flac_to_mp3.sh` — Audio format conversion
- `convert_*.sh` — Various file format converters
- `check_power_on*.sh` — Check power-on hours of disks
- `extract-xiso/` — Xbox ISO extraction tool

---

## 💬 Community Support

**Questions or need help?**  
Join our Discord server for real-time assistance and community discussions:

[Discord Server](https://discord.gg/mGGZdfsera)

---

## 📝 Contributing

Contributions and improvements are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Test your changes** thoroughly on Ubuntu 24.04.3 LTS
3. **Follow existing code style** and documentation patterns (see `.github/copilot-instructions.md`)
4. **Use the shared function library** (`includes/main.sh`) for consistency
5. **Ensure scripts are idempotent** (safe to run multiple times)
6. **Add `set -euo pipefail`** at the top of all bash scripts
7. **Update documentation** for any new features or changes
8. **Submit a Pull Request** with a clear description of your changes

### Code Style Guidelines

- Use `#!/bin/bash` shebang (not `#!/bin/sh`)
- Source `includes/main.sh` for shared functions
- Use `green_echo` for status messages
- Add explicit `exit 0` at script end
- Include shellcheck directives where needed
- Make scripts repo-root-aware (work from any directory)

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include system information and error messages when reporting bugs
- Provide steps to reproduce the issue
- Check existing issues before creating duplicates

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

**Created by:** Adam Matson  
**Purpose:** Linux learning and system administration education  
**Special thanks:** To all contributors and the Linux community  
**Includes:** This product includes software developed by <in@fishtank.com>  
**AI Assistance:** Claude (Anthropic) and GitHub Copilot were used to generate and enhance code  

---

⚠️ **Important**: This guide is a **work-in-progress**. New tools and documentation will be added regularly based on learning objectives and community feedback.

✅ **Status**: Actively maintained and updated for Ubuntu 24.04.3 LTS compatibility.
