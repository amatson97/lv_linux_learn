# Multi-Repository Script System

## Overview

The Multi-Repository Script System provides automated script distribution, updates, and management from multiple sources including GitHub and custom repositories. Scripts are downloaded from remote repositories, cached locally with their includes dependencies, and automatically updated based on configurable intervals.

**Version:** 2.1.1  
**Status:** Production Ready  
**Architecture:** Multi-repository support with GitHub-hosted default manifest and custom manifest capability

## 🆕 Version 2.1.1 Features

### Multi-Repository Support
- **🏗️ Custom Repositories**: Configure custom manifest URLs for your own script libraries
- **📁 Remote Includes**: Automatic download of includes directories from custom repositories  
- **🔄 Cache-First Execution**: Scripts download to cache before execution for optimal performance
- **⚙️ Multi-Repository Management**: Switch between different script repositories seamlessly
- **🔗 Repository URL Support**: Manifests can specify `repository_url` for includes and resources

### Enhanced Features
- **Remote Script Distribution**: Scripts served from GitHub or custom repository raw URLs
- **Automatic Updates**: Configurable auto-check and auto-install with custom repository support
- **Checksum Verification**: SHA256 validation for downloaded scripts
- **Local Caching**: Scripts and includes cached in `~/.lv_linux_learn/script_cache/`
- **Manifest System**: Central registry supporting custom repository configurations
- **Dual Interface**: Full support in both CLI (menu.sh) and GUI (menu.py) with feature parity

## Architecture

### Components

```
lv_linux_learn/
├── manifest.json                    # Master script registry (auto-generated)
├── scripts/generate_manifest.sh     # Manifest generator
├── includes/repository.sh           # Bash backend (500+ lines)
├── lib/repository.py                # Python backend (400+ lines)
├── menu.sh                          # CLI with repository integration
├── menu.py                          # GUI with repository integration
└── .github/workflows/
    └── generate-manifest.yml        # Manual-trigger workflow (disabled)

~/.lv_linux_learn/
├── config.json                      # Repository configuration with custom_manifest_url
├── manifest.json                    # Cached manifest
├── manifest_meta.json               # Metadata (last fetch, etc.)
├── script_cache/                    # Cached scripts and includes by category
│   ├── includes/                    # Remote or symlinked includes directory
│   ├── install/
│   ├── tools/
│   ├── exercises/
│   └── uninstall/
└── logs/
    └── repository.log               # Operation logs
```

### Multi-Repository Data Flow

1. **Configuration**: User sets custom manifest URL or uses default GitHub repository
2. **Manifest Fetch**: System downloads manifest from configured repository URL
3. **Includes Management**: Downloads includes directory from `repository_url` in manifest
4. **Script Distribution**: Scripts downloaded from repository with includes support
5. **Cache-First Execution**: Scripts run from cache with proper includes path setup
6. **Auto-Updates**: Periodic checks for updates from configured repository

## Configuration

### Config File: `~/.lv_linux_learn/config.json`

```json
{
  "version": "1.0.0",
  "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
  "custom_manifest_url": "",
  "use_remote_scripts": true,
  "fallback_to_bundled": false,
  "auto_check_updates": true,
  "auto_install_updates": true,
  "update_check_interval_minutes": 30,
  "last_update_check": null,
  "allow_insecure_downloads": false,
  "cache_timeout_days": 30,
  "verify_checksums": true
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `custom_manifest_url` | `""` | Custom repository manifest URL |
| `use_remote_scripts` | `true` | Enable remote script fetching |
| `auto_check_updates` | `true` | Check for updates on startup |
| `auto_install_updates` | `true` | Automatically download updates |
| `update_check_interval_minutes` | `30` | Minutes between update checks |
| `verify_checksums` | `true` | SHA256 validation |
| `cache_timeout_days` | `30` | Days before cache expires |

### Custom Repository Setup

To use a custom repository, you need:

1. **Manifest file** (`manifest.json`) with repository_url:
```json
{
  "repository_url": "https://raw.githubusercontent.com/youruser/yourrepo/main",
  "version": "1.0.0",
  "scripts": [
    {
      "id": "custom-installer",
      "name": "Custom Software Installer",
      "relative_path": "scripts/custom-installer.sh",
      "category": "install",
      "checksum": "sha256_hash_here"
    }
  ]
}
```

2. **Includes directory** with shared functions:
```
your-repo/
├── manifest.json
├── includes/
│   └── main.sh              # Shared functions
└── scripts/
    └── custom-installer.sh  # Your scripts
```

3. **Configure the system** to use your repository:
- CLI: Menu → Repository → Settings → Custom Manifest URL
- GUI: Repository Tab → Settings → Manifest URL field

### Changing Settings

**CLI (menu.sh)**:
- Main Menu → 6) Script Repository → 6) Repository Settings
- Toggle options with `r`, `c`, `i`
- Set custom manifest URL with `m`
- Change interval with `t`
- Reset to defaults with `d`

**GUI (menu.py)**:
- Repository tab → Settings button
- Dialog with toggles, input fields, and manifest URL configuration
- Changes saved immediately

## Usage

### Setting Up Custom Repositories

#### CLI (menu.sh)

1. **Access Repository Settings**:
   ```bash
   ./menu.sh
   # Select: 6) Script Repository
   # Select: 6) Repository Settings
   ```

2. **Configure Custom Manifest**:
   - Enter your manifest URL when prompted
   - Example: `https://raw.githubusercontent.com/youruser/yourrepo/main/manifest.json`

3. **System will**:
   - Download your manifest
   - Download includes directory from `repository_url`
   - Cache scripts with proper includes support
   - Switch to your repository for script execution

#### GUI (menu.py)

1. **Open Repository Settings**:
   - Click Repository tab
   - Click Settings button

2. **Set Manifest URL**:
   - Enter URL in "Manifest URL" field
   - Click "Reset to Default" to revert to GitHub repository
   - Click OK to save

3. **System will**:
   - Automatically download and configure your repository
   - Update includes and cache as needed
   - Provide feedback in terminal

### Repository Management

#### CLI (menu.sh) Repository Menu
```
1) Update All Scripts         - Download available updates
2) Download All Scripts       - Bulk download all scripts
3) View Cached Scripts        - List local cache contents
4) Clear Script Cache         - Remove all cached files
5) Check for Updates          - Manual refresh
6) Repository Settings        - Configure behavior and custom repositories
```

#### GUI (menu.py) Repository Tab
- **TreeView**: Lists all scripts with:
  - Script Name
  - Category (Install, Tools, Exercises, Uninstall)
  - Version
  - Status (Cached, Not Cached, Update Available)
- **Update All** button - Download all updates
- **Check Updates** button - Refresh status
- **Download All** button - Bulk download
- **Clear Cache** button - Remove cached files
- **Settings** button - Open configuration dialog with custom manifest support

### Cache-First Execution

When running scripts from any interface:

1. **Check Cache**: System checks if script is already cached
2. **User Prompt**: If not cached, prompts user to download first
3. **Download**: Downloads script and includes to cache
4. **Execute**: Runs script from cache with proper includes path
5. **Includes Support**: Automatic includes directory setup for cached scripts

This ensures optimal performance and proper includes functionality for scripts from any repository.

### Programmatic Access (Bash)

```bash
#!/bin/bash
source includes/repository.sh

# Initialize (creates config, directories)
init_repo_config

# Fetch latest manifest
fetch_remote_manifest

# Check for updates
check_for_updates
echo "Updates available: $REPO_UPDATES_AVAILABLE"

# Download specific script
download_script "chrome_install.sh" "scripts/chrome_install.sh"

# Update all scripts
update_all_scripts

# Get cached script path
script_path=$(resolve_script_path "chrome_install.sh")
bash "$script_path"
```

### Programmatic Access (Python)

```python
from lib.repository import ScriptRepository

# Initialize
repo = ScriptRepository()

# Fetch manifest
manifest = repo.fetch_remote_manifest()

# Check updates
updates = repo.check_for_updates()
print(f"Updates available: {len(updates)}")

# Download script
success, path = repo.download_script(
    "chrome_install.sh",
    "scripts/chrome_install.sh"
)

# Update all
downloaded, failed = repo.update_all_scripts()
print(f"Downloaded: {downloaded}, Failed: {failed}")
```

## Manifest Format

### Structure: `manifest.json`

```json
{
  "version": "1.0.0",
  "repository_version": "2.0.0",
  "last_updated": "2025-12-13T16:36:37+00:00",
  "min_app_version": "2.0.0",
  "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
  "scripts": [
    {
      "id": "chrome-install",
      "name": "Chrome Install",
      "category": "install",
      "version": "1.0.0",
      "file_name": "chrome_install.sh",
      "relative_path": "scripts/chrome_install.sh",
      "download_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/scripts/chrome_install.sh",
      "checksum": "sha256:1a9079b012db482bfcd1f0f3d21e3f2c6cfc2c0eba1e31f5ad69c9dbe23842b9",
      "description": "Install Google Chrome (robust, idempotent)",
      "requires_sudo": true,
      "dependencies": [],
      "tags": []
    }
  ]
}
```

### Script Entry Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (kebab-case) |
| `name` | string | Display name |
| `category` | string | `install`, `tools`, `exercises`, `uninstall` |
| `version` | string | Semantic version |
| `file_name` | string | Script filename |
| `relative_path` | string | Path from repo root |
| `download_url` | string | Full GitHub raw URL |
| `checksum` | string | `sha256:<hash>` for verification |
| `description` | string | Purpose/functionality |
| `requires_sudo` | boolean | Needs elevated privileges |
| `dependencies` | array | Required scripts/packages |
| `tags` | array | Metadata tags |

## Maintenance

### Regenerating Manifest

**Manual**:
```bash
cd /home/adam/lv_linux_learn
./scripts/generate_manifest.sh
git add manifest.json
git commit -m "chore: Update manifest"
git push
```

**Automatic**:
- Manual updates pushed to GitHub
- Triggers on push to `scripts/`, `tools/`, `bash_exercises/`, `uninstallers/`
- Manual trigger via GitHub Actions tab

### Adding New Scripts

1. Add script to appropriate directory (`scripts/`, `tools/`, etc.)
2. Include description comment at top:
   ```bash
   #!/bin/bash
   # Description: Install Google Chrome (robust, idempotent)
   ```
3. Commit and push
4. Wait 30 minutes for auto-generation, or run manually:
   ```bash
   ./scripts/generate_manifest.sh
   ```

### Updating Script Versions

1. Modify script
2. Update `VERSION` variable in script (optional):
   ```bash
   VERSION="1.1.0"
   ```
3. Commit and push
4. Manifest auto-updates with new checksum

## Troubleshooting

### Issue: "Failed to download manifest"

**Causes**:
- Repository is private (GitHub raw requires authentication)
- Network connectivity issues
- GitHub CDN propagation delay

**Solutions**:
1. Verify repo is public at [github.com/amatson97/lv_linux_learn/settings](https://github.com/amatson97/lv_linux_learn/settings)
2. Check network: `curl -I https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json`
3. Use cached manifest: `cp manifest.json ~/.lv_linux_learn/manifest.json`
4. Wait 5 minutes for CDN propagation after push

### Issue: "Checksum verification failed"

**Causes**:
- File modified during download
- Manifest out of sync with actual scripts

**Solutions**:
1. Regenerate manifest: `./scripts/generate_manifest.sh`
2. Clear cache: menu.sh → 6 → 4
3. Re-download: menu.sh → 6 → 2

### Issue: "Available scripts: 0"

**Causes**:
- Manifest not in cache location
- Manifest file corrupted

**Solutions**:
1. Copy local manifest: `cp manifest.json ~/.lv_linux_learn/manifest.json`
2. Fetch remote: menu.sh → 6 → 5
3. Check logs: `cat ~/.lv_linux_learn/logs/repository.log | tail -20`

### Issue: Updates not auto-installing

**Verify**:
```bash
# Check config
jq '.auto_install_updates' ~/.lv_linux_learn/config.json

# Should output: true
```

**Fix**:
- CLI: menu.sh → 6 → 6 → i (toggle auto-install)
- GUI: Repository tab → Settings → Enable "Auto-install updates"

## Logging

### Log File: `~/.lv_linux_learn/logs/repository.log`

**Format**:
```
[2025-12-13T16:46:31+00:00] Checking for updates...
[2025-12-13T16:46:31+00:00] Fetching manifest from https://raw.githubusercontent.com/...
[2025-12-13T16:46:31+00:00] ERROR: Failed to download manifest
[2025-12-13T16:46:31+00:00] Failed to fetch manifest, using cached version
```

**View recent entries**:
```bash
tail -50 ~/.lv_linux_learn/logs/repository.log
```

**Clear logs**:
```bash
rm ~/.lv_linux_learn/logs/repository.log
```

## Security

### Checksum Verification
- All downloads validated with SHA256
- Mismatches rejected automatically
- Controlled by `verify_checksums` config

### HTTPS Only
- All downloads over HTTPS
- No insecure HTTP allowed (configurable with `allow_insecure_downloads`)

### Repository Verification
- Scripts must match manifest checksums
- Manifest signed with timestamps
- Audit trail in logs

## API Reference

### Bash Functions (includes/repository.sh)

**Configuration**:
- `init_repo_config()` - Initialize directories and default config
- `load_repo_config()` - Read config.json into memory
- `get_config_value(key, default)` - Get configuration value
- `set_config_value(key, value)` - Update configuration

**Manifest Operations**:
- `fetch_remote_manifest()` - Download from GitHub
- `get_manifest_version()` - Get manifest version string
- `get_script_by_id(id)` - Retrieve script entry by ID
- `list_scripts_by_category(category)` - Filter scripts

**Download & Update**:
- `download_script(filename, relative_path)` - Download single script
- `verify_checksum(file, expected)` - Validate SHA256
- `update_all_scripts()` - Bulk update operation
- `download_all_scripts()` - Bulk download operation
- `check_for_updates()` - Compare local vs remote

**Cache Management**:
- `resolve_script_path(filename)` - Get cached script path
- `get_cached_script_path(filename)` - Check if cached
- `clear_script_cache()` - Remove all cached scripts
- `count_cached_scripts()` - Count cached files
- `list_cached_scripts()` - Display cache contents

### Python Methods (lib/repository.py)

**Class: `ScriptRepository`**

```python
def __init__(self, config_dir=None)
def init_repo_config() -> bool
def load_repo_config() -> dict
def get_config_value(key: str, default=None) -> Any
def set_config_value(key: str, value: Any) -> bool
def fetch_remote_manifest() -> dict
def download_script(filename: str, relative_path: str) -> Tuple[bool, str]
def verify_checksum(filepath: str, expected_checksum: str) -> bool
def update_all_scripts() -> Tuple[int, int]
def download_all_scripts() -> Tuple[int, int]
def check_for_updates() -> list
def resolve_script_path(filename: str) -> str
def clear_script_cache() -> bool
def count_cached_scripts() -> int
def list_cached_scripts() -> list
```

## Performance

### Metrics
- **Manifest fetch**: ~0.5-2s (network dependent)
- **Script download**: ~0.2-1s per script
- **Checksum verification**: <0.1s per script
- **Bulk update (42 scripts)**: ~30-60s

### Optimization
- Scripts cached indefinitely until update
- Manifest cached for `update_check_interval_minutes`
- Parallel downloads not implemented (sequential to avoid rate limits)

## Future Enhancements

### Planned Features
- [ ] Parallel script downloads
- [ ] Rollback to previous versions
- [ ] Script dependency resolution
- [ ] Delta updates (download only changed parts)
- [ ] Signed manifests (GPG verification)
- [ ] Multiple repository sources
- [ ] Script preview before download
- [ ] Bandwidth usage tracking

### Compatibility
- Requires: bash 4.0+, jq, curl
- Tested: Ubuntu 24.04 LTS
- Python GUI: Python 3.8+, GTK 3.0

## Contributing

### Adding Features
1. Modify `includes/repository.sh` for bash backend
2. Mirror changes in `lib/repository.py` for Python backend
3. Update `menu.sh` and `menu.py` integration
4. Test both CLI and GUI
5. Update this documentation

### Testing Checklist
- [ ] Bash syntax check: `bash -n menu.sh`
- [ ] CLI navigation: All repository menu options
- [ ] GUI controls: All buttons functional
- [ ] Download verification: Checksums validate
- [ ] Update detection: Recognizes new versions
- [ ] Settings persistence: Config changes saved
- [ ] Error handling: Graceful failures logged

## Support

**Issues**: [github.com/amatson97/lv_linux_learn/issues](https://github.com/amatson97/lv_linux_learn/issues)  
**Documentation**: [docs/SCRIPT_REPOSITORY.md](./SCRIPT_REPOSITORY.md)  
**Logs**: `~/.lv_linux_learn/logs/repository.log`
