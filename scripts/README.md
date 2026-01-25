# Installation Scripts

This directory contains installation scripts for development tools, applications, and services used in Ubuntu Linux environments.

## Usage

### Via Menu System
The recommended way to run these scripts is through the interactive menu:
```bash
./menu.sh    # CLI interface
./menu.py    # GUI interface
```

### Individual Installers
You can also run individual installation scripts directly:

```bash
./scripts/chrome_install.sh
./scripts/vscode_install.sh
./scripts/sublime_install.sh
./scripts/docker_install.sh
./scripts/install_flatpak.sh
./scripts/install_wine.sh
./scripts/nextcloud_client.sh
./scripts/git_setup.sh
./scripts/new_vpn.sh
```

## What Gets Installed

All installation scripts are idempotent - safe to run multiple times. They check for existing installations and skip unnecessary steps.

### Browsers

**Chrome** (`chrome_install.sh`)
- Google Chrome Stable browser
- Official Google repository and GPG signing key
- Automatic repository updates
- Desktop integration and default browser setup
- Includes architecture validation (amd64 only)

### Development Tools

**Visual Studio Code** (`vscode_install.sh`)
- Microsoft Visual Studio Code editor
- Official Microsoft repository
- GPG key and package signing verification
- Optional development extensions
- System integration and command-line tools

**Sublime Text & Sublime Merge** (`sublime_install.sh`)
- Sublime Text premium code editor
- Sublime Merge visual git client
- Official Sublime HQ repository
- Stable channel updates
- Both editors installed together

**Git & GitHub CLI** (`git_setup.sh`)
- Git version control system
- GitHub CLI (`gh`) for GitHub integration
- Interactive configuration wizard
  - Global user.name and user.email setup
  - GitHub authentication guidance
  - HTTPS recommended for desktop environments
- Optimized for Ubuntu Desktop workflow

**Docker** (`docker_install.sh`)
- Docker Engine (latest stable)
- Docker Compose plugin
- Docker Buildx plugin
- containerd runtime
- User added to `docker` group for non-root access
- Official Docker repository
- Post-installation verification
- System service configuration

### System Tools

**Flatpak** (`install_flatpak.sh`)
- Flatpak universal package system
- GNOME Software Flatpak plugin for GUI integration
- Flathub repository (primary Flatpak app source)
- Flatseal permissions manager
  - Manage Flatpak app permissions
  - Configure filesystem access
  - Control Qt portals and system integration
- Desktop integration with Software Center

**Wine** (`install_wine.sh`)
- Wine Windows compatibility layer
- Winetricks helper tool
- 32-bit architecture support (multilib)
- Microsoft Visual C++ 4.2 MFC Library (mfc42.dll)
- Essential Windows runtime libraries
- Enables running Windows applications and games

### Cloud & Sync

**Nextcloud Desktop Client** (`nextcloud_client.sh`)
- Nextcloud Desktop Client via Flatpak
- File synchronization with Nextcloud servers
- Qt shared memory fix for stability
- Desktop database integration
- System tray integration
- Automatic file sync with selective sync options
- Notification system integration

### Networking & VPN

**ZeroTier VPN** (`new_vpn.sh`)
- ZeroTier VPN client
- Interactive network ID configuration
- Environment variable support (`ZEROTIER_NETWORK_ID`)
- Automatic network joining
- Desktop status icon creation
- Passwordless sudo for zerotier-cli
- Removes conflicting VPNs (NordVPN, Hamachi) automatically
- User-configured networks (no hardcoded IDs)

## Installation Details

### Repository Management
All installers that add third-party repositories:
- Use signed-by keyring approach (modern apt security)
- Store GPG keys in `/etc/apt/keyrings/`
- Create repository files in `/etc/apt/sources.list.d/`
- Update package cache after repository addition

### Architecture Support
- **Chrome**: amd64 only (validates before installation)
- **VS Code**: amd64, arm64, armhf
- **Docker**: amd64, arm64, armhf
- **Other tools**: Follow Ubuntu repository architecture support

### User Permissions
Scripts that modify user groups:
- **Docker**: Adds user to `docker` group (requires logout/reboot)
- **ZeroTier**: Configures sudoers for passwordless zerotier-cli

### Desktop Integration
Scripts create desktop launchers and helper scripts in:
- `~/Desktop/` - Desktop shortcut files
- `~/.lv_connect/` - Helper scripts for status monitoring

Desktop launchers created by:
- ZeroTier (network status)
- NordVPN (VPN status) - if using VPN installer variants

## Prerequisites

Most scripts automatically install their dependencies, but may require:
- Active internet connection
- Sudo/root privileges
- Ubuntu/Debian-based distribution
- Updated package cache (`apt update`)

## Post-Installation

### Requires Logout/Reboot
- **Docker**: Group membership requires logout
- **ZeroTier**: For full integration
- **Flatpak**: For GNOME integration (first-time)

### Configuration Needed
- **Git**: User credentials (prompted interactively)
- **GitHub CLI**: Authentication (`gh auth login`)
- **Nextcloud**: Server connection setup on first launch
- **ZeroTier**: Network authorization at my.zerotier.com

## Safety Features

All installation scripts include:
- Idempotent design (safe to re-run)
- Existing installation detection
- Automatic prerequisite installation
- Error handling and cleanup
- Clear status messages with color coding
- GPG signature verification for repositories
- Architecture compatibility checks

## Uninstallation

All installed applications can be removed using matching uninstallers in the `uninstallers/` directory:

```bash
./uninstallers/uninstall_chrome.sh
./uninstallers/uninstall_vscode.sh
./uninstallers/uninstall_sublime.sh
./uninstallers/uninstall_docker.sh
./uninstallers/uninstall_flatpak.sh
./uninstallers/uninstall_wine.sh
./uninstallers/uninstall_nextcloud.sh
./uninstallers/uninstall_zerotier.sh
```

See [uninstallers/README.md](../uninstallers/README.md) for complete uninstallation documentation.

## Notes

- **Docker**: Non-root access requires logout to activate group membership
- **Git Setup**: Provides guidance for GitHub CLI authentication but doesn't force it
- **Wine**: mfc42.dll installation may fail silently if already present
- **ZeroTier**: Network must be authorized in ZeroTier Central after joining
- **Flatpak**: Flatseal provides GUI for managing sandboxed app permissions
- **Nextcloud**: Includes critical Qt shared memory fix to prevent crashes
- **Repository Updates**: Scripts use official repositories for automatic security updates
- **Compatibility**: Tested on Ubuntu Desktop; may work on other Debian derivatives

## Environment Variables

Some scripts support configuration via environment variables:

- **ZeroTier**: `ZEROTIER_NETWORK_ID` - Network ID to join (skips interactive prompt)

## Related Documentation

- [Uninstallers Documentation](../uninstallers/README.md)
- [Main Repository README](../README.md)
- [Installation Guide](../docs/INSTALLATION.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
