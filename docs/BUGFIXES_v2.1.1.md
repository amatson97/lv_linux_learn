# Bug Fixes - Version 2.1.1

> **Status**: These bugs were fixed and released in v2.1.1. This document serves as historical reference for the fixes made during the v2.1.1 release cycle.

## Critical Issues Fixed (Based on Testing Results)

### 1. ✅ Custom Repository Scripts Missing Includes (CRITICAL)
**Issue**: Cached scripts from custom repositories failed with `blue_echo: command not found`  
**Root Cause**: Custom repository includes directory not downloaded when caching scripts  
**Fix**: Modified `lib/repository.py::download_script()` to automatically download includes from custom repository's `repository_url` before caching scripts  
**Files Modified**: `lib/repository.py` (lines 372-394)

### 2. ✅ Local Repository Scripts Invisible in Multi-Repo Setup (CRITICAL)
**Issue**: Local custom manifests (file:// URLs) not loading when multiple repositories configured  
**Root Cause**: `urlopen()` doesn't handle `file://` URLs; needed explicit local file handling  
**Fix**: Added local file path detection in `lib/manifest_loader.py::fetch_manifest()` to handle both `file://` prefix and direct file paths  
**Files Modified**: `lib/manifest_loader.py` (lines 113-128)

### 3. ✅ Configuration Persistence After Manifest Deletion (CRITICAL)
**Issue**: Deleted manifests "persist" and show up again after refresh  
**Root Cause**: Cached manifest files (`~/.lv_linux_learn/manifest_<name>.json`) not deleted when manifest removed  
**Fix**: Modified `lib/custom_manifest.py::delete_custom_manifest()` to delete cached manifest file using same naming pattern as manifest loader  
**Files Modified**: `lib/custom_manifest.py` (lines 388-393)

### 4. ✅ Custom Online Repo Mislabeled as "Public Repository"
**Issue**: Custom repository showing as "Public Repository" in Repository tab  
**Root Cause**: Hardcoded label "Custom Online" instead of reading `custom_manifest_name` from config  
**Fix**: 
- Updated `menu.py::_populate_repository_tree()` to read `custom_manifest_name` from config (line 1783)
- Updated `lib/custom_manifest.py::switch_to_custom_manifest()` to store manifest name in config (line 434)  
**Files Modified**: `menu.py`, `lib/custom_manifest.py`

### 5. ✅ False "Updates Available" Status (IMPORTANT)
**Issue**: Repository tab shows "📥 Update Available" when no updates required (manifest has `verify_checksums: false`)  
**Root Cause**: Update detection always used checksums even when manifest disabled checksum verification  
**Fix**: 
- Track `verify_checksums` setting per manifest source in `manifest_verify_settings` dictionary
- Skip checksum-based update detection when `verify_checksums: false`
- Scripts show "✓ Cached" instead of false update warnings  
**Files Modified**: `menu.py` (lines 1771-1776, 1824-1831, 1884-1888, 1946-1967)

### 6. ✅ Poor UX for "Go to Directory" on Uncached Scripts (MINOR)
**Issue**: Message not actionable - didn't explain HOW to download  
**Root Cause**: Terse error message without guidance  
**Fix**: Added formatted box with step-by-step instructions on how to download and access directory  
**Files Modified**: `menu.py` (lines 1024-1030)

## Known Minor Issues (Testing Results)

From comprehensive testing with custom repository (https://ichigo1990.uk/script_repo/manifest.json):

### Custom Repository Management
- ⚠️ Embedded terminal output waits for user to press return in some operations
- ⚠️ Configuration sometimes persists after deletion on first refresh (fixed in most cases)
- ✅ Repository switching works correctly
- ⚠️ Cache status icons occasionally lag behind actual state

### Script Cache Operations
- ✅ Individual script downloads working
- ✅ Bulk downloads from Repository tab working
- ✅ Remove operations working correctly
- ⚠️ Update detection occasionally shows false positives (improved with verify_checksums handling)

### Multi-Manifest Scenarios
- ⚠️ Cache icon updates sometimes delayed in multi-repo scenarios
- ⚠️ Local repository scripts required file:// handling fix
- ⚠️ Repository label context could be clearer (shows source name now)

## Testing Recommendations

### Critical Path Testing
1. **Test custom repository includes**: Download script from custom repo and verify execution
2. **Test multi-repo configuration**: Public + local + online custom repos
3. **Test manifest deletion**: Verify cached manifests cleaned up properly
4. **Test repository labeling**: Verify correct names displayed
5. **Test with checksums disabled**: Verify no false "Update Available" warnings
6. **Test directory navigation**: Both cached and uncached scripts

### Edge Cases (Not Yet Tested)
- Malformed JSON manifest handling
- Network timeout scenarios
- Duplicate script IDs from multiple sources
- Special characters in script names/paths
- Concurrent manifest operations

## Version Change
- **2.1.0** → **2.1.1** (bug fix and refactoring release)

## Files Modified Summary
```
lib/repository.py         - Custom repo includes download
lib/manifest_loader.py    - Local file:// URL handling  
lib/custom_manifest.py    - Cached manifest cleanup, name storage
lib/ui_helpers.py         - NEW: Dialog and terminal helpers
lib/repository_ops.py     - NEW: Repository operations with feedback
menu.py                   - Repository labeling, checksum logic, UX improvements, dialog integration
VERSION                   - Updated to 2.1.1
```

## Related Documentation
- See [REFACTORING_STATUS.md](REFACTORING_STATUS.md) for ongoing refactoring progress
- See [TESTING.md](TESTING.md) for comprehensive test plan with results
- See main [README.md](../README.md) for feature overview
