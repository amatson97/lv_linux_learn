# Custom Script System with Multi-Repository Support

## Overview
The Custom Script System allows you to configure custom repositories with their own manifests and includes directories. Custom scripts are managed through repository manifests and integrated inline within existing categories (Install, Tools, Exercises, Uninstall) with cache-first execution. The system supports both GUI (menu.py) and CLI (menu.sh) interfaces with full repository management capabilities.

## Features

### 1. Custom Repository Configuration
- **Configure Custom Repositories**: Point to your own script libraries with manifests
- **Remote Includes Support**: Automatic download of includes directories from custom repositories
- **Multi-Repository Management**: Switch between default and custom repositories seamlessly
- **Cache-First Execution**: Repository scripts download to cache before execution
- **GUI Configuration**: Repository tab → Settings button → Manifest URL field
- **CLI Configuration**: Repository menu → Repository Settings → Custom Manifest URL

### 2. Repository Script Management
- **Download**: Scripts are cached locally before execution in `~/.lv_linux_learn/script_cache/`
- **Update**: Force re-download of scripts and includes from configured repositories
- **Run**: Execute cached scripts with automatic includes resolution
- **Visual Indicators**: Repository scripts show cache status and download progress

### 3. Visual Integration
- Repository scripts appear inline within their assigned categories (Install, Tools, Exercises, Uninstall)
- Cache status indicators show download state
- Scripts maintain consistent interface with built-in scripts
- Category-based organization from manifest.json

## Storage

Repository configuration and cached scripts are stored in:
- **Repository configuration**: `~/.lv_linux_learn/config.json` (includes custom_manifest_url)
- **Repository cache**: `~/.lv_linux_learn/script_cache/` (downloaded scripts with includes)
- **Manifest cache**: `~/.lv_linux_learn/manifest_cache.json` (cached manifest data)

All configuration is persistent across application restarts and shared between CLI and GUI.

## Setting Up Custom Repositories

### Creating Your Repository Structure

1. **Create repository structure**:
```
your-custom-repo/
├── manifest.json
├── includes/
│   └── main.sh              # Shared functions
└── scripts/
    ├── my-installer.sh
    └── my-tool.sh
```

2. **Create manifest.json**:
```json
{
  "version": "1.0.0",
  "repository_url": "https://raw.githubusercontent.com/youruser/yourrepo/main",
  "scripts": [
    {
      "id": "my-custom-installer",
      "name": "My Custom Installer",
      "relative_path": "scripts/my-installer.sh",
      "category": "install",
      "description": "Custom installer for my tools",
      "requires_sudo": true,
      "checksum": "sha256:your_checksum_here"
    },
    {
      "id": "my-custom-tool",
      "name": "My Custom Tool",
      "relative_path": "scripts/my-tool.sh",
      "category": "tools",
      "description": "Custom utility tool",
      "requires_sudo": false,
      "checksum": "sha256:your_checksum_here"
    }
  ]
}
```

3. **Generate checksums** (use update_manifest.sh or manually):
```bash
sha256sum scripts/my-installer.sh
# Add checksum to manifest.json
```

### GUI Repository Configuration

1. Open menu.py
2. Click **Repository** tab
3. Click **Settings** button
4. Enter your manifest URL in "Manifest URL" field:
   ```
   https://raw.githubusercontent.com/youruser/yourrepo/main/manifest.json
   ```
5. Click **OK** to save
6. System automatically downloads your repository manifest
7. Scripts appear in their respective category tabs
8. Click any script to download and execute from cache

### CLI Repository Configuration

```bash
./menu.sh
# Select: 6) Script Repository
# Select: 6) Repository Settings
# Select: m) Set Custom Manifest URL
# Enter: https://raw.githubusercontent.com/youruser/yourrepo/main/manifest.json
# System reloads and shows your custom repository scripts
```

## Repository Script Requirements

### Manifest Requirements
1. **Valid JSON**: manifest.json must be well-formed
2. **Repository URL**: Base URL for downloading scripts and includes
3. **Script Entries**: Each script needs id, name, relative_path, category, checksum
4. **Categories**: Use install, tools, exercises, or uninstall
5. **Checksums**: SHA256 checksums for integrity verification

### Script File Requirements
1. **Must be executable**: `chmod +x your_script.sh`
2. **Must have shebang**: First line should be `#!/bin/bash` (or appropriate interpreter)
3. **Repository structure**: Must be accessible via repository_url + relative_path
4. **Includes support**: Can reference shared functions from includes/ directory

### Recommended Script Pattern

```bash
#!/bin/bash
set -euo pipefail

# Repository-compatible includes sourcing
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

# Source shared functions (works in both local and cached contexts)
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

green_echo "╔════════════════════════════════════════╗"
green_echo "║   Repository Custom Script             ║"
green_echo "╚════════════════════════════════════════╝"

green_echo "[*] Running from repository with includes support..."

# Your script logic here using shared functions

green_echo "[✓] Repository script completed!"
read -p "Press Enter to continue..."
```

## Example Repository Setup

### Complete Example Repository

**Repository Structure:**
```
my-ubuntu-scripts/
├── manifest.json
├── includes/
│   └── main.sh
├── scripts/
│   ├── install/
│   │   └── my_app_installer.sh
│   └── tools/
│       └── system_checker.sh
└── dev_tools/
    └── update_manifest.sh
```

**manifest.json:**
```json
{
  "version": "2.0.0",
  "repository_url": "https://raw.githubusercontent.com/myuser/my-ubuntu-scripts/main",
  "scripts": [
    {
      "id": "my-app-installer",
      "name": "My Application Installer",
      "relative_path": "scripts/install/my_app_installer.sh",
      "category": "install",
      "description": "<b>Custom Application Installer</b>\n\nInstalls and configures my application suite.",
      "requires_sudo": true,
      "checksum": "sha256:abc123..."
    },
    {
      "id": "system-checker",
      "name": "System Health Checker",
      "relative_path": "scripts/tools/system_checker.sh",
      "category": "tools",
      "description": "Checks system health and reports issues",
      "requires_sudo": false,
      "checksum": "sha256:def456..."
    }
  ]
}
```

## Repository Management

### Switching Repositories

**GUI:**
1. Repository tab → Settings
2. Change Manifest URL to new repository
3. Click OK
4. Application reloads with new repository scripts

**CLI:**
1. Main menu → Repository → Settings
2. Set Custom Manifest URL
3. Enter new manifest URL
4. Menu reloads with new scripts

### Updating Repository Scripts

**GUI:**
1. Repository tab → Update button
2. System re-downloads all scripts and includes
3. Cache is refreshed

**CLI:**
1. Main menu → Repository → Update Repository
2. Forces fresh download of manifest and scripts

### Reverting to Default Repository

**GUI:**
1. Repository tab → Settings
2. Clear Manifest URL field (leave empty)
3. Click OK
4. Reverts to built-in lv_linux_learn scripts

**CLI:**
1. Main menu → Repository → Settings
2. Clear Custom Manifest URL
3. System uses default repository

## Benefits

1. **Centralized Management**: Distribute scripts through manifests
2. **Version Control**: Use Git repositories for script versioning
3. **Cache-First**: Fast execution with local caching
4. **Includes Support**: Share common functions across scripts
5. **Integrity Checking**: SHA256 checksums verify downloads
6. **Multi-Repository**: Switch between different script collections
7. **Professional Integration**: Repository scripts work exactly like built-in ones

## Technical Details

### Manifest Structure
```json
{
  "version": "string",
  "repository_url": "base_url_for_downloads",
  "scripts": [
    {
      "id": "unique_identifier",
      "name": "Display Name",
      "relative_path": "path/from/repo/root",
      "category": "install|tools|exercises|uninstall",
      "description": "Markdown-formatted description",
      "requires_sudo": true|false,
      "checksum": "sha256:hexdigest"
    }
  ]
}
```

### Cache Directory Structure
```
~/.lv_linux_learn/
├── config.json                    # Repository configuration
├── manifest_cache.json            # Cached manifest
└── script_cache/
    ├── includes/                  # Downloaded includes
    │   └── main.sh
    └── scripts/                   # Downloaded scripts
        ├── my-installer.sh
        └── my-tool.sh
```

## Troubleshooting

### Repository Not Loading
- **Issue**: Custom repository scripts don't appear
- **Solution**: 
  1. Verify manifest URL is accessible
  2. Check manifest.json is valid JSON
  3. Ensure repository_url is correct
  4. Try Update Repository to force refresh

### Script Download Fails
- **Issue**: Scripts fail to download or execute
- **Solution**: 
  1. Check network connectivity
  2. Verify repository_url + relative_path is accessible
  3. Ensure scripts are executable in repository
  4. Check for firewall or proxy issues

### Checksum Mismatch
- **Issue**: "Checksum verification failed" error
- **Solution**: 
  1. Regenerate checksums in manifest.json
  2. Use update_manifest.sh from dev_tools
  3. Ensure script hasn't been modified since checksum generation

### Includes Not Found
- **Issue**: Scripts can't find shared functions
- **Solution**: 
  1. Verify includes/ directory exists in repository
  2. Check includes are downloaded to cache
  3. Ensure scripts use correct sourcing pattern (see example above)

### Can't Revert to Default Repository
- **Issue**: Stuck on custom repository
- **Solution**: 
  1. Manually edit `~/.lv_linux_learn/config.json`
  2. Remove or clear "custom_manifest_url" field
  3. Restart application

## Creating Distributable Repositories

### Repository Hosting Options

1. **GitHub**: Host public repositories (recommended)
   - Use raw.githubusercontent.com URLs
   - Free for public repositories
   - Version control built-in

2. **GitLab**: Alternative with similar features
   - Use raw.gitlab.com URLs
   - Public or private repositories

3. **Self-Hosted**: Host on your own server
   - Requires web server with HTTPS
   - Full control over access

### Manifest Generation

Use the update_manifest.sh tool to automatically generate manifests:

```bash
# In your custom repository
./dev_tools/update_manifest.sh

# Generates manifest.json with:
# - Script discovery from scripts/ directory
# - Automatic SHA256 checksum generation
# - Category detection from directory structure
# - Description extraction from script comments
```

### Best Practices

1. **Version Your Repository**: Use Git tags for releases
2. **Document Your Scripts**: Add description comments in script headers
3. **Test Locally First**: Verify scripts work in local repository before pushing
4. **Use Consistent Structure**: Follow lv_linux_learn directory layout
5. **Maintain Checksums**: Regenerate manifest after any script changes
6. **Provide README**: Document your repository's purpose and usage

## Future Enhancements

Potential features for future versions:
- Multiple simultaneous repositories
- Repository search and discovery
- Script dependency management
- Automatic update notifications
- Repository ratings and reviews
- Private repository authentication
- Offline repository caching
- Script execution history and logs
