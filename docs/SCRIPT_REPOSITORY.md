# Script Repository System

## Overview

The Script Repository System provides automated script distribution, updates, and management through GitHub. Scripts are downloaded from the remote repository, cached locally, and automatically updated based on configurable intervals.

**Version:** 2.0.0  
**Status:** Production Ready  
**Architecture:** GitHub-based with local caching

## Features

### Core Functionality
- **Remote Script Distribution**: All scripts served from GitHub raw URLs
- **Automatic Updates**: Configurable auto-check and auto-install
- **Checksum Verification**: SHA256 validation for downloaded scripts
- **Local Caching**: Scripts cached in `~/.lv_linux_learn/script_cache/`
- **Manifest System**: Central registry of all scripts with metadata
- **Dual Interface**: Full support in both CLI (menu.sh) and GUI (menu.py)

### Automation
- **GitHub Actions**: Auto-generates manifest every 30 minutes
- **Background Checks**: Periodic update checking based on interval
- **Bulk Operations**: Download or update all scripts at once

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
    └── generate-manifest.yml        # Auto-manifest generation

~/.lv_linux_learn/
├── config.json                      # Repository configuration
├── manifest.json                    # Cached manifest
├── manifest_meta.json               # Metadata (last fetch, etc.)
├── script_cache/                    # Cached scripts by category
│   ├── install/
│   ├── tools/
│   ├── exercises/
│   └── uninstall/
└── logs/
    └── repository.log               # Operation logs
```

### Data Flow

1. **GitHub Actions** runs `generate_manifest.sh` every 30 minutes
2. Manifest committed to repository automatically
3. **menu.sh/menu.py** checks for updates on startup (if enabled)
4. **fetch_remote_manifest()** downloads latest manifest from GitHub
5. **check_for_updates()** compares local vs remote script checksums
6. **download_script()** fetches updated scripts to cache
7. **verify_checksum()** validates downloaded files
8. Scripts executed from cache location

## Configuration

### Config File: `~/.lv_linux_learn/config.json`

```json
{
  "version": "1.0.0",
  "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
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
| `use_remote_scripts` | `true` | Enable remote script fetching |
| `auto_check_updates` | `true` | Check for updates on startup |
| `auto_install_updates` | `true` | Automatically download updates |
| `update_check_interval_minutes` | `30` | Minutes between update checks |
| `verify_checksums` | `true` | SHA256 validation |
| `cache_timeout_days` | `30` | Days before cache expires |

### Changing Settings

**CLI (menu.sh)**:
- Main Menu → 6) Script Repository → 6) Repository Settings
- Toggle options with `r`, `c`, `i`
- Change interval with `t`
- Reset to defaults with `d`

**GUI (menu.py)**:
- Repository tab → Settings button
- Dialog with toggles and input fields
- Changes saved immediately

## Usage

### CLI (menu.sh)

#### Main Menu Options
- **6) Script Repository** - Enter repository management
- **u** - Manually check for updates

#### Repository Menu
```
1) Update All Scripts         - Download available updates
2) Download All Scripts        - Bulk download all 42 scripts
3) View Cached Scripts         - List local cache contents
4) Clear Script Cache          - Remove all cached files
5) Check for Updates           - Manual refresh
6) Repository Settings         - Configure behavior
```

### GUI (menu.py)

#### Repository Tab
- **TreeView**: Lists all scripts with:
  - Script Name
  - Category (Install, Tools, Exercises, Uninstall)
  - Version
  - Status (Cached, Not Cached, Update Available)
- **Update All** button - Download all updates
- **Check Updates** button - Refresh status
- **Download All** button - Bulk download
- **Clear Cache** button - Remove cached files
- **Settings** button - Open configuration dialog

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
- GitHub Action runs every 30 minutes
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
