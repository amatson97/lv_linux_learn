# Installation Guide

Complete guide for installing and configuring tools in the lv_linux_learn repository.

## Table of Contents
1. [Menu Interfaces](#menu-interfaces)
2. [Multi-Repository System](#multi-repository-system)
3. [Installation Scripts](#installation-scripts)
4. [Git Workflow Scripts](#git-workflow-scripts)
5. [Uninstaller System](#uninstaller-system)
6. [Custom Script Management](#custom-script-management)

---

## Menu Interfaces

This repository provides **three ways** to run the setup tool:

### 1. Auto-Launcher (Recommended)
```bash
./launcher.sh
```
Automatically detects your environment and launches:
- **GUI version** (`menu.py`) if running on desktop with GTK installed
- **CLI version** (`menu.sh`) if running over SSH or without GUI

### 2. GUI Menu (Desktop)
```bash
./menu.py
```
**Features:**
- 📦 Install, 🔧 Tools, 📚 Exercises, ⚠️ Uninstall, ℹ️ About tabs
- Embedded VTE terminal for interactive script execution
- Syntax highlighting with descriptions
- Search/filter functionality
- Right-click context menu (copy/paste)
- **✨ Multi-Repository System** - Support for custom script repositories
  - Repository tab for online script management
  - Repository (Local) tab for local file-based scripts
  - Sources tab for managing custom manifest sources
  - Custom manifest URL configuration
  - Automatic includes directory download
  - Cache-first script execution with user prompts
  - See [Custom Script Management](#custom-script-management) for details

**Requirements:** `python3-gi`, `gir1.2-gtk-3.0`, `gir1.2-vte-2.91`

### 3. CLI Menu (Terminal)
```bash
./menu.sh
```
**Features:**
- **Hierarchical category navigation** - Browse by Install, Tools, Exercises, Uninstall, or dynamic categories
- Text-based interactive menu with compact spacing
- **Multi-Repository System** - Full repository management with custom manifest support
- **Custom repositories** - Manage custom script sources via repository menu
- **Repository menu** - Access repository management via option 6
- Works over SSH and headless systems
- No GUI dependencies required
- Full feature parity with GUI version
- Search/filter functionality across all scripts

**Navigation:**
- **Main Menu:** Numbers 1-6 select categories (includes Repository)
- **Category View:** Numbers select scripts, `b` returns to main menu
- **Commands:** `h` help, `s` search, `0` exit

---

## Multi-Repository System

Version 2.3.0 includes comprehensive multi-repository support for both GUI and CLI interfaces.

### Repository Management

#### GUI Repository Tab
- **Repository TreeView**: Shows all scripts with cache status
- **Update All**: Download available updates from configured repository
- **Check Updates**: Refresh status from remote repository
- **Download All**: Bulk download all scripts to cache
- **Clear Cache**: Remove all cached scripts
- **Settings Button**: Configure repository behavior and custom manifest URLs

#### CLI Repository Menu (Option 6)
```
Script Repository Menu:
1) Update All Scripts         - Download available updates
2) Download All Scripts       - Bulk download all scripts
3) View Cached Scripts        - List local cache contents
4) Clear Script Cache         - Remove all cached files
5) Check for Updates          - Manual refresh
6) Repository Settings        - Configure behavior and custom repositories
```

### Custom Repository Configuration

#### Setting Up Custom Repositories

**GUI Configuration:**
1. Open menu.py
2. Click Repository tab
3. Click Settings button
4. Enter custom manifest URL in "Manifest URL" field
5. Click OK to save

**CLI Configuration:**
```bash
./menu.sh
# Select: 6) Script Repository
# Select: 6) Repository Settings
# Select: m) Set Custom Manifest URL
# Enter your repository URL
```

#### Custom Repository Format

Your custom repository should have:

```
your-repo/
├── manifest.json           # Required: Script definitions
├── includes/              # Recommended: Shared functions
│   └── main.sh
└── scripts/               # Your scripts organized by category
    ├── install-tool.sh
    └── utility-script.sh
```

**Example manifest.json:**
```json
{
  "version": "1.0.0",
  "repository_url": "https://raw.githubusercontent.com/youruser/yourrepo/main",
  "scripts": [
    {
      "id": "custom-installer",
      "name": "Custom Software Installer",
      "relative_path": "scripts/install-tool.sh",
      "category": "install",
      "checksum": "sha256:your_checksum_here"
    }
  ]
}
```

### Cache-First Execution

The system now uses cache-first execution for optimal performance:

1. **Cache Check**: System checks if script is already cached locally
2. **User Prompt**: If not cached, prompts user to download first  
3. **Download**: Downloads script and includes to `~/.lv_linux_learn/script_cache/`
4. **Execute**: Runs script from cache with proper includes path setup
5. **Performance**: Subsequent executions use cached version

### Repository Features

- **Automatic Updates**: Configurable auto-check and auto-install
- **Checksum Verification**: SHA256 validation for security
- **Remote Includes**: Automatic download of includes directories
- **Local Caching**: Fast execution with local cache
- **Dual Interface**: Full support in both CLI and GUI
- **Multi-Repository**: Switch between different script repositories

---

## Installation Scripts

All scripts follow consistent patterns:
- **Idempotent:** Safe to run multiple times (checks if already installed)
- **Error handling:** Uses `set -euo pipefail` for robust failure detection
- **Status messages:** Clear feedback using `green_echo` helper function
- **Repo-aware:** Sources shared functions from `includes/main.sh`

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

---

## Git Workflow Scripts

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

---

## Uninstaller System

Safe removal of installed tools with cleanup:

```bash
# Interactive uninstaller menu
./uninstallers/uninstall_menu.sh

# Or run individual uninstallers directly
./uninstallers/uninstall_docker.sh
./uninstallers/uninstall_zerotier.sh
./uninstallers/uninstall_chrome.sh
```

### Available Uninstallers

- `uninstall_zerotier.sh` - Remove ZeroTier VPN (leaves networks first)
- `uninstall_nordvpn.sh` - Remove NordVPN (disconnects & removes group)
- `uninstall_docker.sh` - Remove Docker (warns about data loss)
- `uninstall_chrome.sh` - Remove Google Chrome (optional user data removal)
- `uninstall_sublime.sh` - Remove Sublime Text (optional config removal)
- `uninstall_flatpak.sh` - Remove Flatpak (optional app removal)
- `uninstall_wine.sh` - Remove Wine (optional prefix removal)
- `uninstall_nextcloud.sh` - Remove Nextcloud Client (optional config removal)
- `uninstall_all_vpn.sh` - Remove all VPN tools at once (recommended)
- `clean_desktop_launchers.sh` - Remove desktop icons only

### What Gets Removed

- Installed packages (with `--purge` flag)
- Repository configurations and GPG keys
- System service configurations
- User group memberships
- Desktop launchers and helper scripts
- Optionally: user data and configurations (with confirmation)

See [uninstallers/README.md](../uninstallers/README.md) for detailed documentation.

---

## Custom Script Management

**Manage custom script repositories and sources without editing code!**

### Overview

The system supports three types of script sources:

1. **Public Repository** - Default GitHub-hosted scripts (can be disabled)
2. **Custom Online Repositories** - Your own online manifest URLs
3. **Local File-Based Repositories** - Scripts on your local filesystem

### Adding Custom Sources (GUI)

**Using the Sources Tab:**

1. **Open menu.py** → Click **Sources** tab
2. **Click "Add New Source"** button
3. **Choose method:**
   - **Directory Scan**: Scan local directories for bash scripts
   - **Online Manifest**: Import from a remote manifest.json URL
4. **Fill in details:**
   - Repository Name
   - Description
   - Directory paths (for scan) OR Manifest URL (for online)
5. **Click "Create"** - Your repository appears in Sources tab

**Your scripts will appear in:**
- **Repository** tab (if online source)
- **Repository (Local)** tab (if directory scan)

### Managing Sources (GUI)

**Sources Tab Options:**
- **Edit Selected**: Modify repository details
- **Delete Selected**: Remove custom repositories
- **Refresh List**: Reload all sources

### Custom Repository via Settings

**Alternative method for online repositories:**

1. Open menu.py → Click **Settings** menu
2. Configure:
   - **Use Public Repository**: Enable/disable default GitHub scripts
   - **Custom Manifest URL**: Enter your repository URL
3. Click **OK** to save

### CLI Management

```bash
./menu.sh
# Select: 6) Script Repository
# Select: 6) Repository Settings
# Select: m) Set Custom Manifest URL
# Enter your repository URL
```

### Custom Repository Format

Your custom repository should have:

```
your-repo/
├── manifest.json           # Required: Script definitions
├── includes/              # Recommended: Shared functions
│   └── main.sh
└── scripts/               # Your scripts organized by category
    ├── install/
    ├── tools/
    └── exercises/
```

**Example manifest.json:**
```json
{
  "version": "1.0.0",
  "name": "My Custom Scripts",
  "description": "Personal script collection",
  "repository_url": "https://raw.githubusercontent.com/youruser/yourrepo/main",
  "scripts": [
    {
      "id": "custom-tool",
      "name": "Custom Tool",
      "file_name": "tool.sh",
      "category": "tools",
      "version": "1.0",
      "download_url": "https://raw.githubusercontent.com/youruser/yourrepo/main/scripts/tools/tool.sh",
      "checksum": "sha256:your_checksum_here"
    }
  ]
}
```

### Features

- ✅ **Multiple Sources** - Mix public, custom online, and local repositories
- ✅ **AI Analysis** - Ollama-powered script categorization (if available)
- ✅ **Security** - SHA256 checksum verification for online sources
- ✅ **Cache Management** - Automatic download and caching
- ✅ **Dual Interface** - Full support in both GUI and CLI

### Storage Locations

- Configuration: `~/.lv_linux_learn/config.json`
- Custom manifests: `~/.lv_linux_learn/custom_manifests/`
- Script cache: `~/.lv_linux_learn/script_cache/`

**📖 Full Documentation:** [CUSTOM_SCRIPTS.md](CUSTOM_SCRIPTS.md) | [SCRIPT_REPOSITORY.md](SCRIPT_REPOSITORY.md)

---

## Remote Assistance Installation

⚠️ **Security Warning**: VPN scripts modify system network configuration. Ensure you have local access before running remote assistance tools.

To add your VM to the Linux learning network (facilitated by ZeroTier VPN):

```bash
# Run the VPN setup script (also available in menu)
./scripts/new_vpn.sh
```

**What this script does:**
1. Installs ZeroTier One client
2. Joins a user-configured network (via ZEROTIER_NETWORK_ID env var)
3. Removes conflicting VPN clients if present (NordVPN, Hamachi - legacy)

After installation, enable remote desktop in: **Settings > System > Remote Desktop**

![Remote Settings Screenshot](../images/remote_settings.png "Remote Settings Screenshot")
