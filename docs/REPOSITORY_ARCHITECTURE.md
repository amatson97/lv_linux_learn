# Repository Architecture - Independent Source Design

## Overview

The system now uses a **source-independent architecture** where each repository source (public or custom) operates independently while sharing common infrastructure. This allows multiple sources to coexist without interference.

## Key Architectural Changes (v2.1.1)

### 1. Source Types

Each script belongs to one of these independent source types:

- **`public_repo`**: GitHub-hosted public repository (cached)
- **`custom_repo`**: Online custom manifests (cached)
- **`custom_local`**: Local file-based custom manifests (direct access)
- **`custom_script`**: User-added scripts via CustomScriptManager (direct access)

### 2. Independent Operation

**Before (v2.1.0):** Sources were treated as mutually exclusive or competing:
- Global `use_public_repository` toggle affected all sources
- `custom_manifest_url` in config implied single custom source
- Metadata determined by global config state

**After (v2.1.1):** Each source is independent:
- Sources determined from script metadata (name tags, paths)
- Multiple sources active simultaneously
- No global state dependency for source identification

### 3. Metadata Structure

Scripts now carry self-describing metadata:

```python
{
    "type": "local|cached|remote",           # Availability
    "source_type": "public_repo|custom_repo|custom_local|custom_script",
    "source_name": "Readable identifier",    # e.g., "Public Repository", "Custom: name"
    "source_url": "file:// or https://",     # Origin URL
    "file_exists": bool,                     # For local files
    "is_custom": bool,                       # CustomScriptManager flag
    "script_id": "uuid"                      # Manifest or custom script ID
}
```

### 4. Cache Sharing

**Public and custom online repositories share cache infrastructure:**
- Both use `~/.lv_linux_learn/script_cache/`
- Organized by category (install, tools, etc.)
- No conflicts due to unique script IDs from manifests

**Local sources bypass cache:**
- `custom_local`: Files accessed directly from manifest location
- `custom_script`: User scripts accessed from their locations

## Source Determination Logic

### Script Name Tags
Scripts are tagged with their source in the UI:
- `✓ Script Name [Public Repository]`
- `✓ Script Name [Custom: manifest_name]`
- `📝 Script Name` (custom scripts from CustomScriptManager)

### Metadata Building
The `_build_script_metadata()` function:
1. Checks CustomScriptManager for user-added scripts
2. Parses source tags from script display name
3. Examines file paths for custom manifest directories
4. Checks cache status independently for each source
5. Returns self-contained metadata

## Benefits

### ✅ Independence
- Public repository can be enabled/disabled without affecting custom manifests
- Each custom manifest operates independently
- No global state dependencies

### ✅ Coexistence
- Multiple sources work simultaneously without conflicts
- Shared cache infrastructure for online sources
- Direct file access for local sources

### ✅ Clarity
- Each script knows its source
- UI clearly indicates source with tags
- Right-click menus work for all sources

### ✅ Scalability
- Easy to add new source types
- No modifications needed to existing sources when adding new ones
- Clean separation of concerns

## Implementation Details

### Configuration
```json
{
    "use_public_repository": true,  // Enable/disable public repo
    // No single custom_manifest_url - all in custom_manifests/ directory
}
```

### Manifest Loading
`fetch_manifest()` collects all active sources:
1. Public repository (if enabled)
2. All custom manifests in `~/.lv_linux_learn/custom_manifests/`
3. Returns list of (path, source_name) tuples

### Script Operations

**Download/Update/Remove:**
- Uses script_id to identify script in manifest
- `_get_manifest_script_id()` searches all sources
- Operations aware of source type

**Execution:**
- Local sources: Direct execution from file path
- Cached sources: Execute from cache with includes
- Remote sources: Prompt to download first

**Right-click Context:**
- CustomScriptManager scripts: Edit/Delete
- Repository scripts (any source): Download/Update/Remove from Cache

## Migration Notes

### From v2.1.0 to v2.1.1

**No Breaking Changes:**
- Existing configurations work without modification
- Custom manifests in `custom_manifests/` directory automatically loaded
- Public repository continues to work as before

**Improvements:**
- Better source identification in metadata
- Independent source operation (no interference)
- Clearer UI indication of script sources
- Right-click menus work consistently across all tabs

## Developer Guidelines

### Adding a New Source Type

1. Add new `source_type` value in `_build_script_metadata()`
2. Update source detection logic
3. Determine if source uses cache or direct access
4. Update `_should_use_cache_engine()` if needed
5. No changes needed to other sources

### Testing Source Independence

1. Enable public repository only → Verify scripts load
2. Enable custom manifest only → Verify scripts load
3. Enable both → Verify no conflicts, all scripts load
4. Toggle public repo → Verify custom manifests unaffected
5. Add/remove custom manifests → Verify public repo unaffected

## Future Enhancements

### Potential Improvements
- Per-source cache directories for better isolation
- Source-specific settings (update frequency, checksums, etc.)
- Source priority/override system
- Multi-source script deduplication with priority rules

### Backward Compatibility
All changes maintain backward compatibility with existing configurations and manifests.

---

**Version**: 2.1.1  
**Date**: December 2025  
**Status**: Implemented
