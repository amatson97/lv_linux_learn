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
- Chrome: `~/.config/google-chrome`, `~/.cache/google-chrome`
- Sublime Text: `~/.config/sublime-text`
- Wine: `~/.wine`
- Nextcloud: `~/.config/Nextcloud`, `~/.local/share/Nextcloud`
- Flatpak: All installed applications

### Docker Warning
The Docker uninstaller will warn you before removing:
- All containers
- All images
- All volumes
- All networks

## Safety Features

All uninstallers:
- Check if the package is installed before attempting removal
- Use `--purge` to remove configuration files
- Run `autoremove` to clean up dependencies
- Include error handling to continue even if some steps fail
- Provide clear status messages throughout the process

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
- ZeroTier will leave all networks before uninstalling
- The VPN uninstaller can remove all VPN tools at once
- All scripts are safe to re-run (idempotent)
