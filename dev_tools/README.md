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

### [`verify_docstring_improvements.py`](verify_docstring_improvements.py)
**Purpose:** Validates that enhanced methods have proper docstrings and type hints  
**Usage:** `python3 ./dev_tools/verify_docstring_improvements.py`  
**When to use:** After modifying `lib/repository.py` or any core library files to ensure quality standards

**What it verifies:**
- Comprehensive docstrings (minimum 4 lines including summary, args, returns)
- Type hints on all method parameters and return types
- PEP 257 docstring compliance
- Documentation of critical repository methods
- Documentation of utility module methods

**Methods checked:**
- `ScriptRepository.get_effective_repository_url()`
- `ScriptRepository.get_manifest_url()`
- `ScriptRepository.refresh_repository_url()`
- `ScriptRepository._detect_local_repository()`
- `ScriptRepository._ensure_directories()`
- `ScriptRepository._init_config()`
- `ScriptRepository.list_available_updates()`

**Output format:**
```
✅ method_name()
   Summary: Brief description
   Docstring lines: 8
   ✅ Type hints: True
```

**Exit codes:**
- `0` - All checks passed
- `1` - Some checks failed (warnings shown)

---

### [`test_update_scenario.sh`](test_update_scenario.sh)
**Purpose:** Sets up a local test environment for script update detection verification  
**Usage:** `./dev_tools/test_update_scenario.sh`  
**When to use:** Testing update detection logic without requiring GitHub or network access

**What it does:**
- Creates mock repository structure in temporary directory
- Sets up test manifest files with versioning
- Creates cached scripts with different versions
- Simulates update scenarios locally
- Allows testing of update detection without live repositories
- Cleans up test environment on completion

**Test scenarios covered:**
- No updates available (checksums match)
- Updates available (checksums differ)
- New scripts in manifest (not cached)
- Removed scripts (cached but not in manifest)
- Corrupted cache recovery
- Multiple repository scenarios

**Output:** 
- Test results with pass/fail status
- Details of detected updates
- Cache state information
- Cleanup confirmation

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

3. **Verify code quality:**
   ```bash
   # For Python/library changes
   python3 ./dev_tools/verify_docstring_improvements.py
   
   # For bash script changes
   bash -n scripts/my_new_installer.sh  # Syntax check
   ```

4. **Update and publish manifest:**
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

### Testing Code Changes

Before committing any changes to core library files:

1. **Run type verification:**
   ```bash
   python3 ./dev_tools/verify_docstring_improvements.py
   ```

2. **Run full test suite:**
   ```bash
   cd /home/adam/lv_linux_learn
   python -m pytest tests/ -v
   ```

3. **Test menu integration:**
   ```bash
   ./menu.sh  # CLI menu
   ./menu.py  # GUI menu (if GUI available)
   ```

4. **Check for type errors:**
   ```bash
   pylance check lib/repository.py  # If using Pylance
   ```

### Testing Manifest Changes

1. **Generate updated manifest:**
   ```bash
   ./dev_tools/generate_manifest.sh
   ```

2. **Verify JSON syntax:**
   ```bash
   jq . manifest.json
   ```

3. **Test update detection:**
   ```bash
   ./dev_tools/test_update_scenario.sh
   ```

4. **Commit and push:**
   ```bash
   ./dev_tools/update_manifest.sh
   ```

---

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

---

## 🐛 Troubleshooting

### "Permission denied" errors
```bash
chmod +x dev_tools/*.sh dev_tools/*.py
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

### Docstring verification fails
- Check import paths: `python3 -c "from lib.repository import ScriptRepository"`
- Verify all methods have proper docstrings (see PEP 257 standard)
- Ensure type hints use proper `typing` module types

### Test update scenario fails
- Check temp directory permissions: `ls -la /tmp`
- Verify bash version: `bash --version` (requires 4.0+)
- Ensure manifest.json exists in repository root

---

## 📋 Quick Reference

| Tool | Language | Purpose | Frequency |
|------|----------|---------|-----------|
| `generate_manifest.sh` | Bash | Generate manifest from scripts | Per script change |
| `update_manifest.sh` | Bash | Update manifest + push to GitHub | Per release |
| `verify_docstring_improvements.py` | Python | Validate code quality | Per library change |
| `test_update_scenario.sh` | Bash | Test update detection | Before release |

---

**For more information:** See [CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/](../docs/) directory.