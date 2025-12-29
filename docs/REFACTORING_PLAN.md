# Code Refactoring Plan - lv_linux_learn v2.2

## Current State Analysis

### Issues Identified
1. **menu.py is too large** (6610 lines) - contains business logic that should be in lib/
2. **Overlapping lib modules** - script_handler.py and script_execution.py have overlapping concerns
3. **Scattered manifest logic** - manifest_loader.py, manifest_manager.py, custom_manifest.py
4. **Fallback code in menu.py** - duplicates logic from lib modules
5. **Unclear file naming** - repository_ops.py vs repository.py

### Current lib/ Structure (11 files)
```
lib/
├── __init__.py
├── ai_analyzer.py              # AI script categorization
├── constants.py                # Global constants
├── custom_manifest.py          # Custom manifest creation
├── custom_scripts.py           # CustomScriptManager
├── manifest_loader.py          # Manifest fetching/parsing
├── manifest_manager.py         # Manifest CRUD operations
├── repository_ops.py           # Repository operations (UI-facing)
├── repository.py               # ScriptRepository core class
├── script_execution.py         # Script execution business logic
├── script_handler.py           # Script metadata & cache checking
└── ui_helpers.py               # UI dialog helpers
```

## Proposed Refactoring

### Phase 1: Consolidate Script Management

**Merge:** `script_handler.py` + `script_execution.py` → `script_manager.py`

**Rationale:** These modules both deal with script operations and have overlapping concerns.

**New structure:**
```python
# lib/script_manager.py
"""
Centralized script management - metadata, cache, execution, navigation
"""

class ScriptMetadata:
    """Build and manage script metadata"""
    
class ScriptCache:
    """Cache status checking and path resolution"""
    
class ScriptExecutor:
    """Build execution commands and validate readiness"""
    
class ScriptNavigator:
    """Directory navigation logic"""

# Public API
def get_script_metadata(script_path, category, ...) -> dict
def is_script_cached(repository, script_id, ...) -> bool
def build_execution_command(script_path, metadata, ...) -> str
def get_script_directory(script_path, metadata) -> str
```

### Phase 2: Consolidate Manifest Management

**Merge:** `manifest_loader.py` + `manifest_manager.py` + `custom_manifest.py` → `manifest_service.py`

**Rationale:** All three deal with manifest operations at different levels.

**New structure:**
```python
# lib/manifest_service.py
"""
Unified manifest service - loading, management, custom manifests
"""

class ManifestLoader:
    """Fetch and parse manifest files"""
    
class ManifestRegistry:
    """Manage multiple manifest sources (CRUD)"""
    
class CustomManifestBuilder:
    """Create custom manifests from local directories"""

# Public API
def fetch_manifest(url) -> dict
def load_scripts_from_manifest(repository) -> tuple
def get_local_repository_manifests() -> list
def create_custom_manifest(name, directories, ...) -> bool
```

### Phase 3: Consolidate Repository Operations

**Merge:** `repository.py` + `repository_ops.py` → `repository_service.py`

**Rationale:** repository_ops.py is just a thin wrapper around repository.py.

**New structure:**
```python
# lib/repository_service.py
"""
Complete repository service - core + UI-facing operations
"""

class ScriptRepository:
    """Core repository class (existing)"""
    
class RepositoryOperations:
    """High-level repository operations for UI"""
    
# Public API - combines both modules
```

### Phase 4: Rename for Clarity

**Rename files for clearer purpose:**

```
OLD NAME              → NEW NAME                  PURPOSE
─────────────────────────────────────────────────────────────────
custom_scripts.py     → user_scripts.py          User-added scripts
ui_helpers.py         → dialog_helpers.py        GTK dialog utilities
ai_analyzer.py        → ai_categorizer.py        AI script categorization
constants.py          → config.py                App-wide configuration
```

### Phase 5: Extract Business Logic from menu.py

**Move from menu.py to appropriate lib modules:**

1. **Script operations** → `script_manager.py`
   - `_build_script_metadata()` (already delegated, remove fallback)
   - `_is_script_cached()` (already delegated, remove fallback)
   - `_execute_script_unified()` (keep minimal UI wrapper)
   - `_navigate_to_directory_unified()` (keep minimal UI wrapper)

2. **Repository operations** → `repository_service.py`
   - `_get_all_repository_scripts()`
   - `_download_single_script()`
   - `_update_single_script()`
   - `_remove_script_from_cache()`

3. **Manifest operations** → `manifest_service.py`
   - `_get_manifest_script_id()`
   - Manifest creation/deletion UI logic → keep, but use service

4. **UI-only methods** → Keep in menu.py
   - All GTK-specific methods (widgets, events, dialogs)
   - Terminal feed operations
   - Window management
   - Tab creation

## Final lib/ Structure (7 files)

```
lib/
├── __init__.py                 # Public API exports
├── config.py                   # Constants, settings, paths
├── script_manager.py           # Script metadata, cache, execution
├── manifest_service.py         # Manifest loading, CRUD, custom
├── repository_service.py       # Repository core + operations
├── user_scripts.py             # User-added custom scripts
├── dialog_helpers.py           # GTK dialog utilities
└── ai_categorizer.py           # AI-powered categorization
```

**Reduction:** 11 files → 7 files (36% reduction)

## Implementation Steps

### Step 1: Create New Consolidated Modules
1. Create `lib/script_manager.py` (merge script_handler + script_execution)
2. Create `lib/manifest_service.py` (merge manifest_loader + manifest_manager + custom_manifest)
3. Create `lib/repository_service.py` (merge repository + repository_ops)

### Step 2: Update Imports
1. Update `menu.py` imports to use new modules
2. Update `lib/__init__.py` to export new API
3. Ensure backward compatibility during transition

### Step 3: Remove Old Modules
1. Delete `script_handler.py`
2. Delete `script_execution.py`
3. Delete `manifest_loader.py`
4. Delete `manifest_manager.py`
5. Delete `custom_manifest.py`
6. Delete `repository_ops.py`

### Step 4: Rename Remaining Modules
1. `custom_scripts.py` → `user_scripts.py`
2. `ui_helpers.py` → `dialog_helpers.py`
3. `ai_analyzer.py` → `ai_categorizer.py`
4. `constants.py` → `config.py`

### Step 5: Clean up menu.py
1. Remove all fallback implementations (rely on lib modules)
2. Extract remaining business logic to lib modules
3. Keep only UI-specific code
4. Target: Reduce menu.py to ~3000-4000 lines

### Step 6: Update Documentation
1. Update imports in README.md
2. Update ARCHITECTURE.md
3. Create API documentation for lib modules

## Module Responsibilities (After Refactoring)

### lib/config.py
- Application constants (paths, URLs, defaults)
- Column indices for GTK models
- Configuration loading/saving

### lib/script_manager.py
**Responsibility:** Everything related to individual script operations

- Script metadata building
- Cache status checking
- Execution command building
- Directory navigation
- Environment variable handling
- Script validation

**Key Classes:**
- `ScriptMetadata` - Build/parse metadata
- `ScriptCache` - Cache operations
- `ScriptExecutor` - Execution logic
- `ScriptNavigator` - Directory logic

### lib/manifest_service.py
**Responsibility:** Everything related to manifest files

- Fetching manifests (HTTP/file)
- Parsing manifest JSON
- Loading scripts from manifests
- Managing multiple manifests (CRUD)
- Creating custom manifests
- Manifest validation

**Key Classes:**
- `ManifestLoader` - Fetch/parse
- `ManifestRegistry` - Multi-manifest management
- `CustomManifestBuilder` - Custom manifest creation

### lib/repository_service.py
**Responsibility:** Everything related to the script repository

- Download/update/remove scripts
- Cache management
- Includes synchronization
- Checksum verification
- Repository configuration
- Multi-source aggregation

**Key Classes:**
- `ScriptRepository` - Core functionality
- `RepositoryOperations` - High-level operations

### lib/user_scripts.py
**Responsibility:** User-added custom scripts

- Add/edit/delete custom scripts
- Store in custom_scripts.json
- Separate from manifest system

**Key Classes:**
- `CustomScriptManager` - Manage user scripts

### lib/dialog_helpers.py
**Responsibility:** GTK dialog utilities for menu.py

- Error dialogs
- Confirmation dialogs
- Input dialogs
- Progress dialogs

**Functions:** UI-only helpers

### lib/ai_categorizer.py
**Responsibility:** AI-powered script analysis

- Ollama integration
- Script categorization
- Description generation

**Key Classes:**
- `OllamaAnalyzer` - AI analysis

## Benefits of Refactoring

1. **Clearer separation of concerns** - Each module has one clear purpose
2. **Reduced code duplication** - Remove fallback code from menu.py
3. **Easier testing** - Smaller, focused modules are easier to test
4. **Better maintainability** - Find code faster with logical grouping
5. **Smaller menu.py** - Focused on UI/GTK, easier to navigate
6. **Clearer dependencies** - Module relationships are more obvious
7. **Easier onboarding** - New developers can understand structure faster

## Migration Strategy (Zero Downtime)

1. **Create new modules alongside old ones** - Don't delete anything yet
2. **Update menu.py to import from new modules** - Dual import support
3. **Test thoroughly** - Ensure all functionality works
4. **Remove old modules** - Once new modules are proven stable
5. **Final cleanup** - Remove compatibility shims

## Testing Checklist

After refactoring, verify:

- [ ] Install tab scripts execute correctly
- [ ] Tools tab scripts execute correctly
- [ ] Exercises tab scripts execute correctly
- [ ] Uninstall tab scripts execute correctly
- [ ] Public repository caching works
- [ ] Custom online repository caching works
- [ ] Custom local repository direct execution works
- [ ] User custom scripts direct execution works
- [ ] View script functionality
- [ ] Navigate to directory functionality
- [ ] Download/update/remove from cache
- [ ] Custom manifest creation
- [ ] Repository settings
- [ ] Terminal doesn't block on execution

## Timeline Estimate

- **Phase 1-3 (Consolidation):** 4-6 hours
- **Phase 4 (Renaming):** 1-2 hours
- **Phase 5 (Extract from menu.py):** 3-4 hours
- **Phase 6 (Documentation):** 1-2 hours
- **Testing:** 2-3 hours

**Total:** 11-17 hours of focused development

## Next Steps

1. Review this refactoring plan
2. Approve or request changes
3. Create feature branch: `git checkout -b refactor/lib-consolidation`
4. Implement Phase 1 (script management consolidation)
5. Test and verify Phase 1
6. Continue with subsequent phases
7. Merge to main when complete

---

**Note:** This is a non-breaking refactoring. All existing functionality will be preserved while improving code organization and maintainability.
