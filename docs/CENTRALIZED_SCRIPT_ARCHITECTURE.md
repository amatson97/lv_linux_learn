# Centralized Script Handling Architecture

## Overview

Version 2.1.1 includes a **centralized script handling system** that provides unified logic for managing scripts across all manifest types and dynamic tabs.

## Problem Solved

Previously, script handling logic was scattered across multiple methods, leading to:
- Inconsistent behavior between tabs
- Dynamic tabs not working properly
- Duplicate code for handling local/cached/remote scripts
- Difficult to maintain as features evolved

## Architecture Components

### 1. Script Metadata System

Every script in the liststore now includes JSON metadata (column 4):

```json
{
  "type": "local"|"cached"|"remote",
  "manifest_type": "public"|"custom_online"|"custom_local",
  "source_url": "original URL",
  "file_exists": true|false
}
```

**Building Metadata:** `_build_script_metadata(script_path, category)`
- Called when populating liststore
- Automatically detects script type based on path and cache status
- Determines manifest type from repository configuration

**Retrieving Metadata:** `_get_script_metadata(model, treeiter)`
- Extracts and parses metadata from liststore row
- Returns dict or empty dict on error

### 2. Centralized Execution Logic

**Method:** `_execute_script_unified(script_path, metadata) -> bool`

Handles all three manifest types with consistent logic:

**Local Files (custom_local):**
- Execute directly from source location
- No caching involved
- Example: `file:///home/user/scripts/test.sh`

**Cached Files (public/custom_online):**
- Execute from `~/.lv_linux_learn/script_cache/`
- Ensures includes are available
- Proper working directory context

**Remote Files (public/custom_online):**
- Returns False (not executable yet)
- Caller should offer download dialog
- After download, metadata updates to "cached"

### 3. Centralized Navigation Logic

**Method:** `_navigate_to_directory_unified(script_path, metadata) -> bool`

**Local Files:**
- Opens parent directory of source file
- Uses `xdg-open` for file manager

**Cached Files:**
- Opens cache directory containing script
- Shows cache structure

**Remote Files:**
- Returns False
- Caller should offer download dialog

### 4. Cache Engine Decision Logic

**Method:** `_should_use_cache_engine(metadata) -> bool`

Determines whether to use caching system:

**Returns True (use cache):**
- Public repository scripts (always cached)
- Custom online repository scripts (always cached)

**Returns False (direct execution):**
- Custom local repository scripts (local file:// URLs)

## Manifest Type Handling

### Public Repository (Default GitHub)
- **Type:** `manifest_type: "public"`
- **Scripts:** Always remote initially
- **Cache:** Required for execution
- **Includes:** Downloaded from repository
- **Update:** Automatic with checksum verification

### Custom Online Repository
- **Type:** `manifest_type: "custom_online"`
- **Scripts:** Remote with http/https URLs
- **Cache:** Required for execution
- **Includes:** Downloaded from repository_url
- **Update:** Manual or background check

### Custom Local Repository
- **Type:** `manifest_type: "custom_local"`
- **Scripts:** Local with file:// URLs
- **Cache:** NOT USED - direct execution
- **Includes:** From local filesystem
- **Update:** N/A (always current)

## Dynamic Tab Integration

All tabs (standard and dynamic) use the same centralized methods:

```python
# In _create_script_tab()
for i, script_path in enumerate(scripts):
    metadata = self._build_script_metadata(script_path, tab_name)
    liststore.append([name, path, description, False, json.dumps(metadata)])

# In on_run_clicked()
metadata = self._get_script_metadata(model, treeiter)
success = self._execute_script_unified(script_path, metadata)

# In on_cd_clicked()
metadata = self._get_script_metadata(model, treeiter)
success = self._navigate_to_directory_unified(script_path, metadata)
```

## Cache Icon System

Icons reflect metadata type:

- **✓** Cached (type: "cached") - Script downloaded and ready
- **☁️** Remote (type: "remote") - Needs download
- **📁** Local (type: "local", file_exists: true) - Direct access
- **❌** Missing (type: "local", file_exists: false) - File not found

Icons are determined during `load_scripts_from_manifest()` by checking:
1. If file:// URL → Check if file exists (📁/❌)
2. If cached → Check cache directory (✓)
3. Otherwise → Remote (☁️)

## Benefits

### Consistency
- All tabs use identical logic
- Behavior is predictable across manifest types
- No special cases for dynamic categories

### Maintainability
- Single point of truth for script operations
- Easy to add new features (apply once, works everywhere)
- Clear separation of concerns

### Extensibility
- New manifest types easily supported
- Additional metadata fields simple to add
- Custom handlers can override centralized methods

### User Experience
- Local files execute immediately (no cache)
- Remote files show clear download prompts
- Cache status always accurate and up-to-date

## Migration Notes

**Old Pattern (Scattered Logic):**
```python
def on_run_clicked(self, button):
    if os.path.isfile(script_path):
        # local execution
    elif cached:
        # cached execution
    else:
        # download prompt
```

**New Pattern (Centralized):**
```python
def on_run_clicked(self, button):
    metadata = self._get_script_metadata(model, treeiter)
    success = self._execute_script_unified(script_path, metadata)
    if not success and metadata.get("type") == "remote":
        # offer download
```

## Future Enhancements

The centralized architecture enables:

1. **Remote includes caching** - Cache includes separately per repository
2. **Parallel downloads** - Download multiple scripts at once
3. **Smart updates** - Compare timestamps, not just checksums
4. **Script versioning** - Track multiple versions in cache
5. **Rollback support** - Revert to previous cached versions
6. **Custom handlers** - Per-manifest-type execution logic

## Testing

All manifest types should be tested:

```bash
# Test public repository
./menu.py  # With default GitHub manifest

# Test custom online
export CUSTOM_MANIFEST_URL="https://example.com/manifest.json"
./menu.py

# Test custom local
export CUSTOM_MANIFEST_URL="file:///home/user/manifest.json"
./menu.py
```

Verify:
- ✓ Scripts execute correctly in all tabs
- ✓ Cache icons reflect actual state
- ✓ Local files bypass cache engine
- ✓ Remote files prompt for download
- ✓ Dynamic tabs work identically to standard tabs

## Code Location

**Centralized Methods:** `menu.py` lines ~1115-1290
- `_build_script_metadata()`
- `_get_script_metadata()`
- `_execute_script_unified()`
- `_navigate_to_directory_unified()`
- `_should_use_cache_engine()`

**Integration Points:**
- `_create_script_tab()` - Builds metadata during tab creation
- `on_run_clicked()` - Uses unified execution
- `on_cd_clicked()` - Uses unified navigation
- `on_view_clicked()` - Can use metadata for optimized viewing

## Summary

The centralized script handling architecture provides a **single source of truth** for script operations, ensuring consistent behavior across all manifest types and dynamic tabs. This makes the codebase more maintainable, extensible, and user-friendly.
