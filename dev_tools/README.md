# Development Tools

This directory contains development and maintenance tools for contributors and maintainers.

## 🛠️ Available Tools

### [`generate_manifest.sh`](generate_manifest.sh)
**Purpose:** Scans all script directories and generates `manifest.json`  
**Usage:** `./dev_tools/generate_manifest.sh`  
**When to use:** After adding/removing/modifying scripts in `scripts/`, `tools/`, `bash_exercises/`, or `uninstallers/`

**What it does:**
- Scans all script directories for `.sh` files
- Extracts metadata (description, version, sudo requirements)
- Generates checksums for integrity validation
- Creates `manifest.json` with all script information
- Used by both menu systems to populate script lists

**Output:** Updates `manifest.json` in repository root

---

### [`update_manifest.sh`](update_manifest.sh)
**Purpose:** Complete workflow to update manifest and push to GitHub  
**Usage:** `./dev_tools/update_manifest.sh`  
**When to use:** When you want to publish manifest changes to GitHub

**What it does:**
- Calls `generate_manifest.sh` to update manifest
- Shows detailed diff of changes (added/removed/modified scripts)
- Asks for confirmation before committing
- Commits and pushes to GitHub with descriptive message
- Includes safety checks and backup/restore functionality

**Interactive features:**
- Change visualization (script counts, added/removed/modified)
- Full diff preview option
- Confirmation prompts with ability to cancel
- Automatic backup and restore on cancellation

---

## 📚 Development Workflow

### Adding a New Script

1. **Create your script** in the appropriate directory:
   ```bash
   vim scripts/my_new_installer.sh  # Installation script
   vim tools/my_utility.sh          # Utility tool  
   vim bash_exercises/my_lesson.sh  # Learning exercise
   vim uninstallers/uninstall_something.sh  # Uninstaller
   ```

2. **Test your script locally:**
   ```bash
   chmod +x scripts/my_new_installer.sh
   ./scripts/my_new_installer.sh
   ```

3. **Update and publish manifest:**
   ```bash
   ./dev_tools/update_manifest.sh
   ```

### Script Header Requirements

For proper manifest generation, include these headers in your scripts:

```bash
#!/bin/bash
# Description: Brief description of what this script does
# Author: Your Name (optional)
# Version: 1.0.0
# Requires: sudo, curl, specific-package (if needed)
```

**Important notes:**
- `Description:` line is used for menu display text
- Scripts with `sudo`, `apt`, or `systemctl` are auto-flagged as requiring sudo
- Version defaults to `1.0.0` if not specified

### Testing Changes

Before pushing manifest changes:

1. **Test menu integration:**
   ```bash
   ./menu.sh  # CLI menu
   ./menu.py  # GUI menu (if GUI available)
   ```

2. **Verify script appears correctly:**
   - Check correct category (Install/Tools/Exercises/Uninstall)
   - Verify description is clear
   - Test script execution from menu

3. **Check manifest validity:**
   ```bash
   jq . manifest.json  # Validate JSON syntax
   ```

## 🔧 Future Development Tools (Contribution Opportunities!)

These tools would significantly improve the development experience:

### **Automated Testing Tools**
- **`test_scripts.sh`** - Run syntax checks on all scripts
- **`validate_manifest.sh`** - Verify manifest integrity and links
- **`lint_scripts.sh`** - Run shellcheck on all bash scripts

### **Development Environment Setup**
- **`setup_dev_env.sh`** - Install development dependencies
- **`docker_test_env.sh`** - Spin up Ubuntu test container
- **`pre_commit_setup.sh`** - Configure git hooks for quality checks

### **Quality Assurance**
- **`check_documentation.sh`** - Validate doc links and consistency
- **`security_scan.sh`** - Scan for hardcoded credentials
- **`dependency_check.sh`** - Verify script requirements are documented

**Want to contribute any of these tools?** See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines!

## 🐛 Troubleshooting

### "Permission denied" errors
```bash
chmod +x dev_tools/*.sh
```

### "jq: command not found" 
```bash
sudo apt install -y jq
```

### Git push errors
- Ensure you have push permissions to the repository
- Check if you're on the correct branch: `git branch`
- Verify remote is set: `git remote -v`

### Manifest generation fails
- Check script syntax: `bash -n scripts/your_script.sh`
- Verify script headers include `# Description:` line
- Ensure script directories exist and contain `.sh` files

---

**For more information:** See [CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/](../docs/) directory.