# Uninstallers

This directory contains removal scripts for all tools installed by lv_linux_learn.

## Usage

### Interactive Menu
Run the uninstaller menu for a guided experience:
```bash
./uninstallers/uninstall_menu.sh
```

### Individual Uninstallers
You can also run individual uninstaller scripts directly:

```bash
./uninstallers/uninstall_zerotier.sh
./uninstallers/uninstall_nordvpn.sh
./uninstallers/uninstall_docker.sh
./uninstallers/uninstall_chrome.sh
./uninstallers/uninstall_vscode.sh
./uninstallers/uninstall_sublime.sh
./uninstallers/uninstall_flatpak.sh
./uninstallers/uninstall_wine.sh
./uninstallers/uninstall_nextcloud.sh
./uninstallers/uninstall_all_vpn.sh
./uninstallers/clean_desktop_launchers.sh
```

## What Gets Removed

Each uninstaller removes:
- The installed package(s)
- Associated repositories and GPG keys
- System service configurations
- User group memberships (where applicable)
- Desktop launchers and helper scripts

### Optional Removals
Some uninstallers will prompt you before removing user data:
- **Chrome**: `~/.config/google-chrome`, `~/.cache/google-chrome` (bookmarks, history, passwords, extensions)
- **VS Code**: `~/.vscode/extensions`, `~/.config/Code` (extensions, settings, workspace data)
- **Sublime Text**: `~/.config/sublime-text`, `~/.config/sublime-merge` (settings, packages, licenses)
- **Wine**: `~/.wine` (Windows application data and installed programs)
- **Nextcloud**: `~/.config/Nextcloud`, `~/.local/share/Nextcloud` (sync configuration and local files)
- **Flatpak**: All installed applications (including Flatseal), Flathub repository, and user data (`~/.local/share/flatpak`)

### VPN Cleanup
VPN uninstallers provide complete network restoration:
- **ZeroTier**: Leaves all networks before uninstalling, removes service and configuration
- **NordVPN**: Disconnects active connections, removes nordvpn group membership, disables meshnet
- **All VPNs**: Comprehensive removal of ZeroTier, NordVPN, and LogMeIn Hamachi in one operation

### Docker Warning
The Docker uninstaller will warn you before removing:
- All containers (running and stopped)
- All images
- All volumes
- All networks
- Docker Compose plugin
- User from docker group

## What Gets Removed

Each uninstaller provides comprehensive cleanup:

### Common Removals (All Scripts)
- Package removal with `--purge` flag
- Repository configuration files
- GPG keys and keyrings
- Automatic dependency cleanup (`autoremove`)
- Desktop launchers and helper scripts from `~/.lv_connect`

### Specific Uninstallers

**Chrome**
- Google Chrome Stable package
- `/etc/apt/sources.list.d/google-chrome.list`
- Optional: User profile data

**VS Code**
- Visual Studio Code package
- Microsoft repository and GPG key
- Optional: Extensions, settings, and workspace data

**Docker**
- Docker Engine (CE), CLI, containerd
- Docker Compose and Buildx plugins
- Docker service (stopped and disabled)
- `/var/lib/docker` data directory
- User removed from docker group

**Flatpak**
- Flatpak runtime
- GNOME Software plugin
- Flatseal permissions manager
- Flathub repository
- All installed Flatpak applications (with confirmation)
- `/var/lib/flatpak` and `~/.local/share/flatpak`

**Wine**
- All wine packages and winetricks
- WineHQ repository (if added)
- Optional: Wine prefix (`~/.wine`) with Windows applications

**Sublime Text**
- Sublime Text editor and Sublime Merge
- Sublime HQ repository
- Support for apt, snap, and flatpak installations
- Optional: User settings and package data

**Nextcloud**
- Nextcloud Desktop Client (apt or flatpak)
- Nextcloud repository
- Flatpak desktop database entries
- Optional: Sync configuration and local data

**ZeroTier**
- Leaves all networks before uninstall
- ZeroTier service (stopped and disabled)
- Sudoers configuration
- Desktop status icons

**NordVPN**
- Disconnects and logs out before removal
- Disables meshnet
- Removes nordvpn group and user membership
- Repository and configuration
- Desktop status icons

**All VPN**
- Calls individual uninstallers for ZeroTier and NordVPN
- Also removes LogMeIn Hamachi if installed
- Complete network restoration

**Desktop Launchers**
- All `.desktop` files from `~/Desktop` created by lv_linux_learn
- Helper scripts directory (`~/.lv_connect`)
- Does not uninstall applications

## Safety Features

All uninstallers:
- Check if the package is installed before attempting removal
- Use `--purge` to remove configuration files
- Run `autoremove` to clean up dependencies
- Include error handling (`|| true`) to continue even if some steps fail
- Provide clear status messages throughout the process
- Use confirmation dialogs before destructive operations
- Exit gracefully if user cancels operation

## Desktop Launchers

To remove only desktop icons and helper scripts without uninstalling the applications:
```bash
./uninstallers/clean_desktop_launchers.sh
```

This removes:
- All `.desktop` files from `~/Desktop`
- Helper scripts from `~/.lv_connect`

## Notes

- Some uninstallers may require a reboot to fully remove group memberships (Docker, NordVPN)
- ZeroTier leaves all networks automatically before uninstalling
- The All VPN uninstaller removes ZeroTier, NordVPN, and LogMeIn Hamachi
- Flatpak uninstaller prompts before removing applications; choosing "No" cancels the entire operation
- VS Code uninstaller handles extensions and settings separately from the main package
- Sublime Text uninstaller supports apt, snap, and flatpak installations
- Nextcloud uninstaller detects installation method (apt or flatpak) automatically
- All scripts are safe to re-run (idempotent)
- User data removal is always optional and requires explicit confirmation
