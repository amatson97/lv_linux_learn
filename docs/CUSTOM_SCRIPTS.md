# Custom Script Addition Feature

## Overview
The Custom Script Addition feature allows you to add your own scripts to the menu.py GUI without editing Python code. This makes the tool more flexible and personalized to your workflow.

## Features

### 1. Add Custom Scripts
- Click the **+** button on any tab header (Install, Tools, Exercises, or Uninstall)
- Fill in the script details:
  - **Script Name**: Display name that will appear in the list
  - **Script Path**: Full path to your executable script file, or browse with the **Browse...** button
  - **Description**: Markdown-formatted description with formatting support:
    - `<b>Bold</b>` for bold text
    - `<tt>monospace</tt>` for code/file paths
    - Bullet points with `•`
  - **Requires sudo**: Check if your script needs sudo privileges

### 2. Manage Custom Scripts
- **Edit**: Right-click on any custom script (marked with 📝) and select "✏️ Edit Script"
- **Delete**: Right-click and select "🗑️ Delete Script" (confirms before deletion)
- **Run**: Double-click or click "Run Script in Terminal" (works just like built-in scripts)

### 3. Visual Indicators
- Custom scripts are marked with a 📝 emoji prefix
- Built-in scripts have no prefix
- Right-click menu only appears for custom scripts

## Storage

Custom scripts are stored in:
- **Configuration file**: `~/.lv_linux_learn/custom_scripts.json`
- **Scripts directory**: `~/.lv_linux_learn/scripts/` (for scripts you create within the GUI)

The configuration is persistent across application restarts.

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

## Script Requirements

For a script to work properly:
1. **Must be executable**: `chmod +x your_script.sh`
2. **Must have shebang**: First line should be `#!/bin/bash` (or appropriate interpreter)
3. **Should use `green_echo`**: Source `includes/main.sh` for consistent output formatting

## Example Custom Script Template

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
