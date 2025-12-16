# Local Repository Path Resolution Fix (v2.1.1)

## Problem

Prior to this fix, when creating a custom manifest from local script directories, the system was:
1. **Copying** all scripts to `~/.lv_linux_learn/custom_scripts/<manifest_name>/`
2. Creating `file://` URLs pointing to these **copied** scripts
3. Setting `repository_url` to the copied location

This caused several issues:
- Scripts were duplicated unnecessarily
- Changes to original scripts weren't reflected in the application
- Disk space wasted on duplicate copies
- Users lost track of which version was "canonical"
- Scripts weren't executing from their intended development location

## Solution

The manifest creation logic has been rewritten to:
1. **NOT copy** scripts - they remain in their original location
2. Create `file://` URLs pointing directly to the **original** script paths
3. Set `repository_url` to the actual script directory
4. Store only manifest metadata in `~/.lv_linux_learn/custom_manifests/`

## Technical Details

### Files Modified

#### `lib/custom_manifest.py`

**Line ~200-237**: Changed script handling logic
```python
# OLD (BAD): Copied scripts to ~/.lv_linux_learn/custom_scripts/
dest_path = scripts_dir / dest_filename
shutil.copy2(source_path, dest_path)
manifest_scripts[category].append({
    "download_url": f"file://{dest_path}",
    ...
})

# NEW (CORRECT): References original location
manifest_scripts[category].append({
    "download_url": f"file://{source_path}",  # Original path
    ...
})
```

**Line ~180**: Removed unnecessary script directory creation
```python
# OLD: Created directory for script copies
scripts_dir = self.custom_scripts_dir / name
scripts_dir.mkdir(exist_ok=True)

# NEW: Only create manifest directory
manifest_dir = self.custom_manifests_dir / name
manifest_dir.mkdir(exist_ok=True)
```

**Line ~243**: Updated repository_url
```python
# OLD: Pointed to copy location
"repository_url": f"file://{scripts_dir}"

# NEW: Points to actual script directory
"repository_url": f"file://{primary_scan_dir}"
```

**Line ~347-373**: Updated delete method (backward compatibility)
```python
# Added note about backward compatibility with old manifests
# If scripts_dir exists from older versions, still delete it
if scripts_dir.exists():
    shutil.rmtree(scripts_dir)  # Clean up old copies
```

**Line ~643-648**: Updated rename method (backward compatibility)
```python
# Only rename scripts_dir if it exists (for old manifests)
if (self.custom_scripts_dir / old_name).exists():
    (self.custom_scripts_dir / old_name).rename(new_scripts_dir)
```

### Manifest Structure

**Before Fix:**
```json
{
  "repository_url": "file:///home/user/.lv_linux_learn/custom_scripts/my_manifest",
  "scripts": {
    "category": [{
      "download_url": "file:///home/user/.lv_linux_learn/custom_scripts/my_manifest/script.sh"
    }]
  }
}
```

**After Fix:**
```json
{
  "repository_url": "file:///home/user/my_scripts",
  "scripts": {
    "category": [{
      "download_url": "file:///home/user/my_scripts/script.sh"
    }]
  }
}
```

## Testing

### Test Case 1: Create Local Manifest

```bash
# Create test directory with scripts
mkdir -p /tmp/my_scripts
cat > /tmp/my_scripts/test.sh << 'EOF'
#!/bin/bash
# Description: Test script
# Category: testing
echo "Test script"
EOF
chmod +x /tmp/my_scripts/test.sh

# Create manifest via GUI or Python API
python3 << 'PYTHON'
import sys
sys.path.insert(0, '/home/user/lv_linux_learn')
from lib.custom_manifest import CustomManifestCreator

creator = CustomManifestCreator()
success, msg = creator.create_manifest(
    name="test_manifest",
    scan_directories=["/tmp/my_scripts"],
    recursive=False
)
print(msg)
PYTHON

# Verify manifest points to original location
cat ~/.lv_linux_learn/custom_manifests/test_manifest/manifest.json | \
  jq -r '.scripts | .[] | .[].download_url'
# Should output: file:///tmp/my_scripts/test.sh

# Verify NO copies were made
ls ~/.lv_linux_learn/custom_scripts/
# Should be empty or not contain test_manifest directory
```

### Test Case 2: Verify Execution from Original Location

```python
# In menu.py, local scripts should:
# 1. Show 📄 icon (not ☁️)
# 2. Execute directly from file:// path
# 3. Not attempt caching
# 4. Reflect changes immediately when source script is edited
```

## Backward Compatibility

The fix maintains backward compatibility:

1. **Old manifests** (created before this fix):
   - Still reference `~/.lv_linux_learn/custom_scripts/`
   - Will continue to work
   - Can be deleted with cleanup of copied scripts

2. **New manifests** (created after this fix):
   - Reference original script locations
   - No copies created
   - More efficient and maintainable

3. **Migration**: No automatic migration needed. Users can:
   - Keep old manifests as-is
   - Delete and recreate to get new behavior
   - Manually edit manifest JSON if desired

## Benefits

1. **No duplication**: Scripts stay in one place
2. **Live updates**: Changes to scripts are immediately reflected
3. **Disk space**: No wasted space on copies
4. **Developer workflow**: Scripts execute from development location
5. **Clear separation**: Manifest metadata separate from script storage
6. **Caching logic**: Local scripts properly bypass cache system

## Related Files

- [lib/custom_manifest.py](../lib/custom_manifest.py) - Manifest creation logic
- [menu.py](../menu.py) - UI integration and execution
- [lib/manifest_loader.py](../lib/manifest_loader.py) - Manifest loading
- [docs/CUSTOM_SCRIPTS.md](CUSTOM_SCRIPTS.md) - User documentation

## See Also

- [REPOSITORY_ARCHITECTURE.md](REPOSITORY_ARCHITECTURE.md) - Overall system design
- [CUSTOM_SCRIPTS_IMPLEMENTATION.md](CUSTOM_SCRIPTS_IMPLEMENTATION.md) - Implementation details
