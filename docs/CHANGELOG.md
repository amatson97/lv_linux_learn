# Changelog — lv_linux_learn

## Version 2.2.3 — Debug Logging Removal and UX Polish

**Release Date:** December 29, 2025  
**Focus:** Remove verbose cache debug logging; keep behavior clean and consistent

### Summary

This patch release removes the temporary "CACHE-DEBUG" logging across the GUI and Python library modules. Runtime output is now quiet and focused on user-facing messages. Functional behavior remains the same, including auto-download and cache-first execution.

### Changes

- Removed CACHE-DEBUG prints in:
  - menu.py
  - lib/repository.py
  - lib/manifest_loader.py
  - lib/script_manager.py
  - lib/script_execution.py
- Preserved all functional behavior (no API changes)
- Kept repository operation logs in `~/.lv_linux_learn/logs/repository.log`

### Notes

- For troubleshooting, prefer checking the log file:
  - `tail -50 ~/.lv_linux_learn/logs/repository.log`
- The test harness remains available and passes:
  - `/home/adam/lv_linux_learn/.venv/bin/python tests/run_tests.py`

### Validation

- Test suite: 19 tests passed, 0 failures
- Manual run validations: GUI and CLI flows remain functional

---

## Version 2.2.2 — Architecture Refactoring

**Release Date:** December 16, 2024  
**Version:** 2.2.2  
**Focus:** Major architecture refactoring for cleaner design and better maintainability

### 🎯 Major Changes

#### Architecture Simplification

**Removed Dynamic Category Tabs**
- Eliminated scattered custom/AI/network/security category tabs
- Consolidated all scripts into four main categories: Install, Tools, Exercises, Uninstall
- Cleaner UI with consistent navigation

**New Repository-First Architecture**
```
Repository (Online) → Shows all online scripts (public + custom online)
Repository (Local)  → Shows all local file-based scripts
         ↓
    AI Categorization
         ↓
Install | Tools | Exercises | Uninstall
  (Filtered views from all sources)
```

#### Smart Script Categorization

**AI-Powered Organization**
- Integrated Ollama AI for intelligent script categorization
- Automatic categorization based on script content and purpose
- Heuristic fallback when AI unavailable
- Scripts from all sources appear in appropriate category tabs

**Categorization Logic**
- Install: apt install, yum install, pip install, docker pull, setup scripts
- Uninstall: apt remove/purge, cleanup operations
- Tools: File conversion, backup, extraction, system utilities
- Exercises: Learning scripts, tutorials, practice examples

#### Repository Views

**Repository (Online) Tab**
- Displays all online script sources
- Public repository (GitHub)
- Custom online repositories
- Cache status indicators (☁️ remote, ✓ cached)
- One-click download and execution

**Repository (Local) Tab**  
- Shows all local file-based repositories
- Direct execution (no caching)
- AI analysis for categorization
- Read-only view (no double-click execution)
- Use control buttons for actions

### 🐛 Bug Fixes

**Duplicate Script Prevention**
- Fixed: Local repository scripts appearing twice
- Cause: `script_ids_seen` initialized after first scan
- Solution: Shared duplicate tracking across both scan methods

**Error Resolution**
- Fixed: `NON_STANDARD_CATEGORIES` undefined errors
- Removed: All 16+ references to obsolete dynamic category system
- Result: ~200+ lines of dead code removed

**UI Consistency**
- Fixed: Repository (Local) double-click execution
- Changed: Users must use control buttons instead
- Reason: Prevents accidental script execution

### ⚡ Performance Improvements

**Code Cleanup**
- Removed redundant `NON_STANDARD_CATEGORIES` global dictionary
- Eliminated `_ensure_dynamic_tabs_exist()` method (62 lines)
- Removed dynamic category creation loops
- Simplified tab switching logic
- Cleaned up redundant widget getters

**Maintainability**
- Clearer separation of concerns
- Repository tabs = source views
- Category tabs = filtered views
- Easier debugging and testing

### 📊 Statistics

**Code Changes**
- Files modified: 1 (menu.py)
- Lines removed: ~250
- Lines added: ~150
- Net reduction: ~100 lines
- Methods removed: 3
- Global variables removed: 1

---

## Previous Releases

For complete release history, see the [GitHub releases page](https://github.com/amatson97/lv_linux_learn/releases).
