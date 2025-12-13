# Linux Learning Guide

![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04.3%20LTS-orange)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
![Scripts](https://img.shields.io/badge/Scripts-44-blue)
![Public](https://img.shields.io/badge/Status-Public-brightgreen)

> **🎯 Target Environment:** Ubuntu Desktop 24.04.3 LTS  
> **🔒 Security Scope:** Personal machines and servers at your own risk - review scripts before execution  
> **🌟 Public Repository:** Open source project welcoming contributions!

---

## 🚀 Quick Start

**New to Linux? Get started in 3 steps:**

```bash
# 1. Clone this repository
sudo apt update && sudo apt install -y gh
git config --global user.name "YOUR_USERNAME"
git config --global user.email "YOUR_EMAIL"
gh auth login --hostname github.com --web
gh repo clone amatson97/lv_linux_learn
cd lv_linux_learn

# 2. Make scripts executable
chmod +x scripts/*.sh includes/*.sh tools/*.sh zerotier_tools/*.sh ai_fun/*.sh *.sh

# 3. Run the menu (auto-detects GUI or CLI)
./launcher.sh
```

**Or run specific interface:**
- `./menu.py` — GUI version (GTK desktop app)
- `./menu.sh` — CLI version (terminal-based)

---

## 📚 What's Inside

### 🎯 Core Features
- **🖥️ Interactive Menus** — GUI and CLI interfaces with hierarchical navigation
- **☁️ GitHub Integration** — Auto-updating script distribution from public repository
- **📦 Installation Scripts** — Automated setup for Docker, Chrome, Git, VPN, and more
- **🔧 Custom Scripts** — Add your own scripts without editing code
- **🎓 Learning Exercises** — Interactive bash tutorials for beginners
- **🛠️ Utility Tools** — File conversion, extraction, and system utilities
- **🤖 AI Integration** — Perplexity CLI with streaming and context support
- **🌐 Network Tools** — ZeroTier VPN monitoring and management
- **🔒 Security Focused** — Best practices for localhost development environments

### 📦 Installation Scripts
Install common tools with one command:
- Docker (engine + CLI + compose)
- Google Chrome
- Git + GitHub CLI
- Flatpak + Flathub
- Wine + Winetricks
- Sublime Text
- Nextcloud Client
- ZeroTier VPN

### 🔧 Utilities & Tools
- Archive extractors (7z, zip, rar, xiso)
- Media converters (FLAC→MP3)
- Git workflow helpers
- Disk health checkers
- Bash learning exercises

### 📖 Documentation Structure
```
docs/
├── INSTALLATION.md          # Menu interfaces & installation scripts
├── DOCKER.md                # Docker, Portainer, Plex setup
├── TROUBLESHOOTING.md       # System diagnostics & problem solving
├── NETWORKING.md            # ZeroTier VPN & network tools
├── TOOLS.md                 # Utilities & bash exercises
├── AI_TOOLS.md              # Perplexity CLI & desktop apps
├── ADVANCED.md              # Traefik, Nextcloud, GitHub
├── TOKEN_GUIDE.md           # API tokens & credentials
├── CUSTOM_SCRIPTS.md        # Custom script addition guide
├── CUSTOM_SCRIPTS_QUICKSTART.md
└── CUSTOM_SCRIPTS_IMPLEMENTATION.md
```

---

## 📖 Documentation

### Essential Guides
- **[Installation Guide](docs/INSTALLATION.md)** — Menu interfaces, scripts, custom script addition
- **[Docker Guide](docs/DOCKER.md)** — Containers, compose, Portainer, Plex
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** — Diagnostics and problem solving
- **[API Tokens & Credentials](docs/TOKEN_GUIDE.md)** — NordVPN, ZeroTier, and other API tokens
- **[Package Manager (apt)](#-package-manager-apt)** — Essential apt commands

### Specialized Topics
- **[Networking & VPN](docs/NETWORKING.md)** — ZeroTier tools and monitoring
- **[Tools & Utilities](docs/TOOLS.md)** — File tools and bash exercises
- **[AI Integration](docs/AI_TOOLS.md)** — Perplexity CLI and desktop apps
- **[Advanced Topics](docs/ADVANCED.md)** — Traefik, Nextcloud, GitHub workflows

### Learning Resources
- **[Beginner Resources](#-beginner-resources--tools)** — VMware, tutorials, command references
- **[Linux Drive Management](docs/TOOLS.md#linux-drive-management)** — Formatting, mounting, RAID

---

## 📦 Package Manager (apt)

The **apt** package manager is the primary tool for installing, updating, and managing software on Ubuntu.

### Common Commands

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade

# Install a package
sudo apt install <package-name>

# Remove a package (keeps config files)
sudo apt remove <package-name>

# Remove package and config files
sudo apt purge <package-name>

# Search for packages
apt search <keyword>

# Show package details
apt show <package-name>

# Clean apt cache
sudo apt clean
```

### Quick Tips
- Always `sudo apt update` before installing
- Combine update and upgrade: `sudo apt update && sudo apt upgrade`
- List installed packages: `apt list --installed`
- See upgradable packages: `apt list --upgradable`

📖 **Full Guide:** [Apt User Guide](https://help.ubuntu.com/community/AptGet/Howto)

---

## 📖 Beginner Resources & Tools

### Essential Downloads
- [VMware Workstation Pro FREE](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true) (Sign up required)
- [Balena Etcher USB Imager](https://etcher.balena.io)
- [Ubuntu Desktop Install Guide](https://ubuntu.com/tutorials/install-ubuntu-desktop#1-overview)

### Learning Resources
- [Useful Linux Command Reference](https://www.hostinger.com/tutorials/linux-commands)
- [Linux Journey - Basic Concepts](https://linuxjourney.com/)
- [Command Lookup](https://explainshell.com/)
- [Chmod Calculator](https://chmod-calculator.com/)

---

## 💬 Community Support

**Need help?** Join our Discord server:

[Discord Server](https://discord.gg/mGGZdfsera)

---

## 📝 Contributing

Contributions welcome! Please:
1. Fork and create a feature branch
2. Test on Ubuntu 24.04.3 LTS
3. Follow existing code style (see `.github/copilot-instructions.md`)
4. Use `includes/main.sh` for shared functions
5. Add `set -euo pipefail` to bash scripts
6. Update documentation for changes
7. Update manifest: `./scripts/generate_manifest.sh` (auto-updates every 30 min)
8. Submit a Pull Request

### Reporting Issues
- Use GitHub Issues for bugs/features
- Include system info and error messages
- Provide reproduction steps
- Check existing issues first

---

## 🌐 Remote Repository System (v2.0.0+)

**Automated script distribution from GitHub with local caching.**

### Features
- **Auto-updates**: Scripts automatically downloaded from GitHub
- **Checksum Verification**: SHA256 validation for security
- **Local Caching**: Fast execution with `~/.lv_linux_learn/script_cache/`
- **Configurable**: Auto-check intervals, auto-install options
- **Dual Interface**: Full CLI and GUI support

### Quick Usage
```bash
# CLI: Access repository menu
./menu.sh
# Select: 6) Script Repository

# GUI: Repository tab
./menu.py
# Click: Repository tab → Check Updates
```

### Configuration
Edit settings via menu or directly:
```bash
# Location: ~/.lv_linux_learn/config.json
# Toggle auto-updates, change intervals, etc.

# CLI: Main Menu → 6 → 6 (Repository Settings)
# GUI: Repository tab → Settings button
```

### Documentation
- **Full Guide**: [docs/SCRIPT_REPOSITORY.md](docs/SCRIPT_REPOSITORY.md)
- **Manifest**: [manifest.json](manifest.json) (auto-generated)
- **Backend**: [includes/repository.sh](includes/repository.sh), [lib/repository.py](lib/repository.py)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🤝 Contributing

This is a **public open-source project** welcoming contributions! 

### Quick Contribute
```bash
# Fork repository
gh repo fork amatson97/lv_linux_learn --clone

# Create feature branch  
git checkout -b feature/my-script

# Add your script to appropriate directory
# Follow the guidelines in CONTRIBUTING.md

# Test and submit PR
```

### What We Need
- 📦 **New installers** for popular Ubuntu software
- 🛠️ **Utility scripts** for common tasks  
- 🎓 **Learning exercises** for bash beginners
- 📖 **Documentation** improvements
- 🐛 **Bug fixes** and testing

See [**CONTRIBUTING.md**](CONTRIBUTING.md) for detailed guidelines.

## 📋 Project Policies

- **🔒 [Security Policy](SECURITY.md)** — Vulnerability reporting & best practices
- **🤝 [Contributing Guide](CONTRIBUTING.md)** — How to add scripts & features  
- **📜 [Code of Conduct](CODE_OF_CONDUCT.md)** — Community standards

## 🐛 Issues & Support

- **🐛 Bug Reports:** [GitHub Issues](https://github.com/amatson97/lv_linux_learn/issues/new?template=bug_report.yml)
- **✨ Feature Requests:** [GitHub Issues](https://github.com/amatson97/lv_linux_learn/issues/new?template=feature_request.yml)  
- **🔒 Security Issues:** [Security Advisories](https://github.com/amatson97/lv_linux_learn/security/advisories/new)
- **💬 Discussions:** [GitHub Discussions](https://github.com/amatson97/lv_linux_learn/discussions)
- **📖 Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 🙏 Credits

**Created by:** Adam Matson  
**Purpose:** Linux learning and system administration education  
**Special thanks:** To all contributors and the Linux community  
**Includes:** Software developed by <in@fishtank.com>  
**AI Assistance:** Claude (Anthropic) and GitHub Copilot  

---

⚠️ **Status:** Work-in-progress | Actively maintained for Ubuntu 24.04.3 LTS
