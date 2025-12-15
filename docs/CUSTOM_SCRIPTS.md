# Custom Script System with Multi-Repository Support

## Overview
The Custom Script System allows you to add your own scripts and configure custom repositories in both GUI and CLI interfaces. Custom scripts are integrated inline within existing categories (Install, Tools, Exercises, Uninstall) and marked with a 📝 emoji. This system also supports complete custom script repositories with their own manifests and includes directories.

## Features

### 1. Local Custom Scripts
- **GUI**: Click the **+** button on any tab header (Install, Tools, Exercises, or Uninstall) to add scripts to that category
- **CLI**: Custom scripts are managed through the main menu system and appear inline with manifest scripts
- Fill in script details:
  - **Script Name**: Display name that will appear in the list
  - **Script Path**: Full path to your executable script file, or browse with the **Browse...** button
  - **Description**: Markdown-formatted description with formatting support
  - **Requires sudo**: Check if your script needs sudo privileges

### 2. Custom Repository Configuration
- **Configure Custom Repositories**: Point to your own script libraries with manifests
- **Remote Includes Support**: Automatic download of includes directories from custom repositories
- **Multi-Repository Management**: Switch between different script repositories seamlessly
- **GUI Configuration**: Repository tab → Settings button → Manifest URL field
- **CLI Configuration**: Repository menu → Repository Settings → Custom Manifest URL

### 3. Manage Custom Scripts
- **Edit**: Right-click on any custom script (marked with 📝) and select "✏️ Edit Script"
- **Delete**: Right-click and select "🗑️ Delete Script" (confirms before deletion)
- **Run**: Double-click or click "Run Script in Terminal" (works just like built-in scripts)
- **Cache-First Execution**: Repository scripts download to cache before execution

### 4. Visual Indicators
- Custom scripts are marked with a 📝 emoji prefix and appear inline within their assigned categories
- Repository scripts show cache status indicators
- Built-in scripts have no prefix
- Right-click menu only appears for custom scripts (marked with 📝)

## Storage

Custom scripts and repository configuration are stored in:
- **Local custom scripts**: `~/.lv_linux_learn/custom_scripts.json`
- **Repository configuration**: `~/.lv_linux_learn/config.json` (includes custom_manifest_url)
- **Repository cache**: `~/.lv_linux_learn/script_cache/` (downloaded scripts with includes)
- **Scripts directory**: `~/.lv_linux_learn/scripts/` (for scripts you create within the GUI)

All configuration is persistent across application restarts and shared between CLI and GUI.

## Example Usage

### Adding a Custom Script

1. Click the **+** button on the Tools tab
2. Enter details:
   ```
   Script Name: My Backup Tool
   Script Path: /home/user/scripts/backup.sh
   Description:
   <b>Automated Backup Script</b>
   Script: <tt>/home/user/scripts/backup.sh</tt>
   
   • Creates compressed backups of important directories
   • Uploads to remote storage
   • <b>Requirements:</b> rsync, tar packages
   
   Requires sudo: ☑ (checked)
   ```
3. Click OK
4. Your script appears in the Tools tab with 📝 prefix

### Editing a Custom Script

1. Right-click on "📝 My Backup Tool"
2. Select "✏️ Edit Script"
3. Update any fields (name, path, description, sudo)
4. Click OK to save changes

### Deleting a Custom Script

1. Right-click on the custom script
2. Select "🗑️ Delete Script"
3. Confirm deletion
4. Script is removed from the menu (actual file is NOT deleted)

### Setting Up Custom Repositories

#### Creating Your Repository Structure

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
      "checksum": "sha256:your_checksum_here"
    }
  ]
}
```

3. **Configure in application**:
- **GUI**: Repository tab → Settings → Manifest URL field
- **CLI**: Main menu → Repository → Settings → Custom Manifest URL

#### CLI Repository Configuration

```bash
./menu.sh
# Select: 6) Script Repository
# Select: 6) Repository Settings
# Select: m) Set Custom Manifest URL
# Enter: https://raw.githubusercontent.com/youruser/yourrepo/main/manifest.json
```

#### GUI Repository Configuration

1. Open menu.py
2. Click Repository tab
3. Click Settings button
4. Enter your manifest URL in "Manifest URL" field
5. Click OK to save
6. System automatically downloads your repository and includes

## Script Requirements

### Local Custom Scripts
1. **Must be executable**: `chmod +x your_script.sh`
2. **Must have shebang**: First line should be `#!/bin/bash` (or appropriate interpreter)
3. **Should use `green_echo`**: Source `includes/main.sh` for consistent output formatting

### Repository Scripts
1. **All above requirements plus**:
2. **Manifest entry**: Must be defined in manifest.json with correct checksum
3. **Repository structure**: Must follow repository_url + relative_path pattern
4. **Includes support**: Can use shared functions from repository's includes/ directory

## Example Custom Script Templates

### Local Custom Script

```bash
#!/bin/bash

# Source shared functions for green_echo
if [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    source "$HOME/lv_linux_learn/includes/main.sh"
fi

green_echo "╔════════════════════════════════════════╗"
green_echo "║   My Custom Script                     ║"
green_echo "╚════════════════════════════════════════╝"

green_echo "[*] Starting custom operation..."

# Your script logic here

green_echo "[✓] Operation completed!"
read -p "Press Enter to continue..."
```

### Repository-Compatible Script

```bash
#!/bin/bash

# Repository scripts can use includes/ directory
# Works for both local repository and cached execution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES_DIR="$SCRIPT_DIR/../includes"

# Try multiple locations for includes
if [ -f "$INCLUDES_DIR/main.sh" ]; then
    source "$INCLUDES_DIR/main.sh"
elif [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    source "$HOME/lv_linux_learn/includes/main.sh"
else
    echo "Warning: Could not find shared functions"
fi

green_echo "╔════════════════════════════════════════╗"
green_echo "║   Repository Custom Script             ║"
green_echo "╚════════════════════════════════════════╝"

green_echo "[*] Running from repository with includes support..."

# Your script logic here using shared functions

green_echo "[✓] Repository script completed!"
read -p "Press Enter to continue..."
```

## Benefits

1. **No Code Editing**: Add scripts without modifying Python code
2. **Organized Categories**: Place scripts in appropriate tabs
3. **Persistent**: Scripts remain available across restarts
4. **Easy Management**: Edit and delete through GUI
5. **Professional Integration**: Custom scripts work exactly like built-in ones

## Technical Details

### Data Structure
Each custom script is stored with:
- `id`: Unique UUID identifier
- `name`: Display name
- `category`: Tab category (install/tools/exercises/uninstall)
- `script_path`: Absolute path to script file
- `description`: Markdown description
- `requires_sudo`: Boolean flag
- `created_date`: ISO 8601 timestamp
- `is_custom`: Always true for custom scripts

### JSON Example
```json
{
  "scripts": [
    {
      "id": "abc123-def456-...",
      "name": "My Backup Tool",
      "category": "tools",
      "script_path": "/home/user/scripts/backup.sh",
      "description": "<b>Automated Backup</b>\n• Creates backups\n• Uploads to cloud",
      "requires_sudo": true,
      "created_date": "2024-12-11T23:00:00",
      "is_custom": true
    }
  ]
}
```

## Troubleshooting

### Script Not Appearing
- **Issue**: Added script doesn't show up
- **Solution**: Check that the script file exists and is executable

### Can't Run Script
- **Issue**: Script fails to execute
- **Solution**: 
  1. Verify script has proper shebang (`#!/bin/bash`)
  2. Check file permissions (`chmod +x script.sh`)
  3. Test script directly in terminal first

### Lost Custom Scripts
- **Issue**: Scripts disappeared after restart
- **Solution**: Check `~/.lv_linux_learn/custom_scripts.json` exists and is valid JSON

### Right-Click Menu Not Showing
- **Issue**: Can't edit or delete script
- **Solution**: Only custom scripts (with 📝 prefix) have right-click menus. Built-in scripts cannot be edited.

## Future Enhancements

Potential features for future versions:
- Import/export custom script configurations
- Share custom scripts with other users
- Script templates and wizard
- Syntax highlighting in script editor
- Inline script creation (no external file needed)
- Script validation and testing within GUI
