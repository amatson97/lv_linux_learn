"""Custom manifest creation and management for LV Script Manager"""

import json
import os
import hashlib
import shutil
import tempfile
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ScriptScanner:
    """Scans directories for executable shell scripts and extracts metadata"""
    
    def __init__(self):
        self.script_extensions = ['.sh', '.bash']
        self.executable_patterns = ['#!/bin/bash', '#!/bin/sh', '#!/usr/bin/env bash']
    
    def is_executable_script(self, file_path: Path) -> bool:
        """Check if file is a shell script (doesn't require execute permission)"""
        if not file_path.is_file():
            return False
            
        # Check file extension
        if file_path.suffix not in self.script_extensions:
            return False
        
        # Check shebang line (scripts will be executed with bash, so executable bit not required)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                return any(pattern in first_line for pattern in self.executable_patterns)
        except Exception:
            return False
    
    def extract_script_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract metadata from script headers using same logic as generate_manifest.sh"""
        metadata = {
            'name': file_path.stem,
            'description': '',
            'version': '1.0.0',
            'category': 'custom'
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Extract Description (multi-line support)
            description_lines = []
            in_description = False
            
            for line in lines[:50]:  # Only check first 50 lines
                line = line.strip()
                
                # Start of description
                if line.startswith('# Description:'):
                    desc_content = line[len('# Description:'):].strip()
                    if desc_content:
                        description_lines.append(desc_content)
                    in_description = True
                    continue
                
                # Continue description if we're in it
                if in_description:
                    if line.startswith('#') and not line.startswith('##'):
                        # Remove leading # and whitespace
                        desc_line = re.sub(r'^#\s*', '', line)
                        if desc_line:
                            description_lines.append(desc_line)
                        elif description_lines:  # Empty comment line ends description
                            break
                    elif line == '' and description_lines:
                        # Empty line ends description
                        break
                    elif not line.startswith('#'):
                        # Non-comment line ends description
                        break
                
                # Look for other metadata
                if line.startswith('# Version:'):
                    metadata['version'] = line[len('# Version:'):].strip()
                elif line.startswith('# Category:'):
                    metadata['category'] = line[len('# Category:'):].strip().lower()
            
            # Join description lines
            if description_lines:
                metadata['description'] = ' '.join(description_lines)
            else:
                # Fallback: create description from filename
                name_parts = file_path.stem.replace('_', ' ').replace('-', ' ').split()
                metadata['description'] = f"Custom script: {' '.join(word.capitalize() for word in name_parts)}"
        
        except Exception as e:
            print(f"Warning: Could not extract metadata from {file_path}: {e}")
            metadata['description'] = f"Custom script: {file_path.stem}"
        
        return metadata
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Dict[str, any]]:
        """Scan directory for scripts and return list of script info"""
        scripts = []
        
        if not directory.exists() or not directory.is_dir():
            return scripts
        
        # Get all files to scan
        if recursive:
            file_pattern = directory.rglob('*')
        else:
            file_pattern = directory.glob('*')
        
        for file_path in file_pattern:
            if self.is_executable_script(file_path):
                metadata = self.extract_script_metadata(file_path)
                
                # Calculate relative path from scan directory
                try:
                    relative_path = file_path.relative_to(directory)
                except ValueError:
                    # File is outside directory (shouldn't happen with rglob)
                    continue
                
                script_info = {
                    'id': file_path.stem,
                    'name': metadata['name'],
                    'description': metadata['description'],
                    'version': metadata['version'],
                    'category': metadata['category'],
                    'file_path': str(file_path),
                    'relative_path': str(relative_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                scripts.append(script_info)
        
        return scripts

class CustomManifestCreator:
    """Creates and manages custom script manifests using file:// URLs"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".lv_linux_learn"
        self.custom_manifests_dir = self.config_dir / "custom_manifests"
        self.custom_scripts_dir = self.config_dir / "custom_scripts"
        self.config_file = self.config_dir / "config.json"
        
        # Initialize directories
        self.custom_manifests_dir.mkdir(parents=True, exist_ok=True)
        self.custom_scripts_dir.mkdir(parents=True, exist_ok=True)
        
        self.scanner = ScriptScanner()
    
    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def create_manifest(self, name: str, scan_directories: List[str], 
                       description: str = "", recursive: bool = True, verify_checksums: bool = True) -> Tuple[bool, str]:
        """Create a custom manifest from scanned directories"""
        try:
            # Validate inputs
            if not name or not name.replace('_', '').replace('-', '').isalnum():
                return False, "Manifest name must contain only letters, numbers, hyphens, and underscores"
            
            # Create manifest directory (only need manifest storage, not script copies)
            manifest_dir = self.custom_manifests_dir / name
            manifest_dir.mkdir(exist_ok=True)
            
            # Scan all provided directories
            all_scripts = []
            categories = set()
            
            for dir_path in scan_directories:
                directory = Path(dir_path).expanduser().resolve()
                if not directory.exists():
                    print(f"Warning: Directory does not exist: {directory}")
                    continue
                
                scripts = self.scanner.scan_directory(directory, recursive)
                all_scripts.extend(scripts)
                categories.update(script['category'] for script in scripts)
            
            if not all_scripts:
                return False, "No executable scripts found in specified directories"
            
            # Create manifest with file:// URLs pointing to original locations
            # DO NOT copy scripts - they should execute from their original paths
            manifest_scripts = {}
            
            # Use the first scan directory as the repository_url base
            # This ensures relative path resolution works correctly
            primary_scan_dir = Path(scan_directories[0]).expanduser().resolve()
            
            for script in all_scripts:
                source_path = Path(script['file_path'])
                
                # Calculate checksum of original file
                checksum = self.calculate_file_checksum(source_path)
                
                # Update script info for manifest
                category = script['category']
                if category not in manifest_scripts:
                    manifest_scripts[category] = []
                
                manifest_scripts[category].append({
                    "id": script['id'],
                    "name": script['name'],
                    "description": script['description'],
                    "version": script['version'],
                    "download_url": f"file://{source_path}",  # Point to ORIGINAL location
                    "checksum": checksum,
                    "size": script['size'],
                    "last_modified": script['modified']
                })
            
            # Create manifest structure
            manifest = {
                "manifest_version": "2.1.0",
                "repository_name": name,
                "repository_description": description or f"Custom script collection: {name}",
                "repository_url": f"file://{primary_scan_dir}",  # Point to actual script directory
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "total_scripts": len(all_scripts),
                "categories": sorted(list(categories)),
                "verify_checksums": verify_checksums,
                "scripts": manifest_scripts
            }
            
            # Save manifest
            manifest_file = manifest_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return True, f"Created manifest '{name}' with {len(all_scripts)} scripts"
            
        except Exception as e:
            return False, f"Failed to create manifest: {e}"
    
    def list_custom_manifests(self) -> List[Dict[str, any]]:
        """List all created custom manifests"""
        manifests = []
        
        if not self.custom_manifests_dir.exists():
            return manifests
        
        for item in self.custom_manifests_dir.iterdir():
            manifest_info = None
            
            # Handle directory-based manifests (from directory scanning)
            if item.is_dir():
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest_data = json.load(f)
                        
                        manifest_info = {
                            'name': item.name,
                            'description': manifest_data.get('repository_description', ''),
                            'version': manifest_data.get('version', '1.0.0'),
                            'created': manifest_data.get('created', ''),
                            'total_scripts': manifest_data.get('total_scripts', 0),
                            'categories': manifest_data.get('categories', []),
                            'manifest_path': str(manifest_file),
                            'type': 'directory_scan',
                            'verify_checksums': manifest_data.get('verify_checksums', True)
                        }
                    except Exception as e:
                        print(f"Warning: Could not load manifest {item.name}: {e}")
            
            # Handle direct JSON files (from URL imports)
            elif item.is_file() and item.suffix == '.json':
                try:
                    with open(item, 'r') as f:
                        manifest_data = json.load(f)
                    
                    # Handle imported URL manifests (new structure)
                    imported_metadata = manifest_data.get('_imported_metadata')
                    if imported_metadata:
                        scripts = manifest_data.get('scripts', [])
                        
                        # Count scripts and categories
                        if isinstance(scripts, dict):
                            total_scripts = sum(len(scripts_list) for scripts_list in scripts.values())
                            categories = list(scripts.keys())
                        else:
                            total_scripts = len(scripts)
                            categories = list(set(script.get('category', 'unknown') for script in scripts))
                        
                        manifest_info = {
                            'name': imported_metadata.get('name', item.stem),
                            'description': imported_metadata.get('description', ''),
                            'version': manifest_data.get('version', '1.0.0'),
                            'created': imported_metadata.get('imported_at', ''),
                            'total_scripts': total_scripts,
                            'categories': categories,
                            'manifest_path': str(item),
                            'type': 'imported_url',
                            'source_url': imported_metadata.get('imported_from', ''),
                            'verify_checksums': imported_metadata.get('verify_checksums', manifest_data.get('verify_checksums', True))
                        }
                    
                    # Handle old imported URL manifests (legacy structure)
                    elif manifest_data.get('type') == 'imported_url':
                        original_manifest = manifest_data.get('original_manifest', {})
                        scripts = original_manifest.get('scripts', [])
                        
                        # Count scripts and categories
                        if isinstance(scripts, dict):
                            total_scripts = sum(len(scripts_list) for scripts_list in scripts.values())
                            categories = list(scripts.keys())
                        else:
                            total_scripts = len(scripts)
                            categories = list(set(script.get('category', 'unknown') for script in scripts))
                        
                        manifest_info = {
                            'name': manifest_data.get('name', item.stem),
                            'description': manifest_data.get('description', ''),
                            'version': manifest_data.get('version', '1.0.0'),
                            'created': manifest_data.get('created', ''),
                            'total_scripts': total_scripts,
                            'categories': categories,
                            'manifest_path': str(item),
                            'type': 'imported_url',
                            'source_url': manifest_data.get('source_url', '')
                        }
                except Exception as e:
                    print(f"Warning: Could not load manifest {item.name}: {e}")
            
            if manifest_info:
                manifests.append(manifest_info)
        
        return sorted(manifests, key=lambda x: x['name'])
    
    def delete_custom_manifest(self, name: str) -> Tuple[bool, str]:
        """Delete a custom manifest and its associated data
        
        Note: For local manifests created with v2.1.1+, scripts remain in their
        original location. Only the manifest metadata is deleted.
        For older manifests, any copied scripts are also removed.
        """
        try:
            # Check for directory-based manifest (from directory scanning)
            manifest_dir = self.custom_manifests_dir / name
            scripts_dir = self.custom_scripts_dir / name
            
            # Check for direct JSON file (from URL imports)
            direct_manifest_file = self.custom_manifests_dir / f"{name}.json"
            
            manifest_existed = False
            
            # Delete directory-based manifest
            if manifest_dir.exists():
                # Remove scripts directory if it exists (backward compatibility)
                # Note: v2.1.1+ doesn't create this, but older versions did
                if scripts_dir.exists():
                    shutil.rmtree(scripts_dir)
                
                # Remove manifest directory
                shutil.rmtree(manifest_dir)
                manifest_existed = True
            
            # Delete direct JSON file manifest
            if direct_manifest_file.exists():
                direct_manifest_file.unlink()
                manifest_existed = True
            
            if not manifest_existed:
                return False, f"Manifest '{name}' does not exist"
            
            # CRITICAL: Delete cached manifest file to prevent persistence
            config_dir = Path.home() / '.lv_linux_learn'
            # Create cache filename using same pattern as manifest_loader.py
            cache_filename = f"manifest_{name.lower().replace(' ', '_')}.json"
            cached_manifest = config_dir / cache_filename
            if cached_manifest.exists():
                cached_manifest.unlink()
                print(f"[DEBUG] Deleted cached manifest: {cached_manifest}")
            
            # Check if this was the active manifest and clear it
            config = self._load_config()
            current_url = config.get('custom_manifest_url', '')
            
            # Check if current manifest URL points to this manifest
            if (f"/{name}/manifest.json" in current_url or 
                f"/{name}.json" in current_url):
                # Clear the custom manifest URL to revert to default
                config['custom_manifest_url'] = ''
                self._save_config(config)
            
            return True, f"Deleted manifest '{name}'"
            
        except Exception as e:
            return False, f"Failed to delete manifest: {e}"
    
    def switch_to_custom_manifest(self, name: str) -> Tuple[bool, str]:
        """Switch application to use a custom manifest"""
        try:
            # Check for directory-based manifest first (from directory scanning)
            manifest_dir = self.custom_manifests_dir / name
            manifest_file = manifest_dir / "manifest.json"
            
            # Check for direct JSON file (from URL imports)
            direct_manifest_file = self.custom_manifests_dir / f"{name}.json"
            
            if manifest_file.exists():
                # Directory-based manifest
                file_url = f"file://{manifest_file}"
            elif direct_manifest_file.exists():
                # Direct JSON file manifest
                file_url = f"file://{direct_manifest_file}"
            else:
                return False, f"Manifest '{name}' does not exist"
            
            # Load current config
            config = self._load_config()
            
            # Update config to use custom manifest
            config['custom_manifest_url'] = file_url
            config['custom_manifest_name'] = name  # Store the manifest name for display
            
            # Save updated config
            self._save_config(config)
            
            return True, f"Switched to custom manifest '{name}'"
            
        except Exception as e:
            return False, f"Failed to switch manifest: {e}"
    
    def switch_to_default_manifest(self) -> Tuple[bool, str]:
        """Switch back to default GitHub manifest"""
        try:
            config = self._load_config()
            
            # Remove custom manifest URL
            if 'custom_manifest_url' in config:
                del config['custom_manifest_url']
            
            self._save_config(config)
            
            # Clear environment variable if set
            if 'CUSTOM_MANIFEST_URL' in os.environ:
                del os.environ['CUSTOM_MANIFEST_URL']
            
            return True, "Switched to default manifest"
            
        except Exception as e:
            return False, f"Failed to switch to default: {e}"
    
    def get_current_manifest_info(self) -> Dict[str, any]:
        """Get information about currently active manifest"""
        try:
            config = self._load_config()
            
            # Check for custom manifest URL
            custom_url = os.environ.get('CUSTOM_MANIFEST_URL', 
                                      config.get('custom_manifest_url', ''))
            
            if custom_url:
                if custom_url.startswith('file://'):
                    # Local custom manifest
                    manifest_path = custom_url[7:]  # Remove 'file://' prefix
                    manifest_file = Path(manifest_path)
                    
                    if manifest_file.exists():
                        with open(manifest_file, 'r') as f:
                            manifest_data = json.load(f)
                        
                        return {
                            'type': 'custom_local',
                            'name': manifest_data.get('repository_name', 'Unknown'),
                            'description': manifest_data.get('repository_description', ''),
                            'url': custom_url,
                            'version': manifest_data.get('version', '1.0.0'),
                            'total_scripts': manifest_data.get('total_scripts', 0)
                        }
                else:
                    # Remote custom manifest
                    return {
                        'type': 'custom_remote',
                        'name': 'Custom Repository',
                        'url': custom_url,
                        'description': 'Remote custom script repository'
                    }
            
            # Default manifest
            return {
                'type': 'default',
                'name': 'LV Linux Learn',
                'description': 'Official lv_linux_learn script repository',
                'url': 'https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json'
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'name': 'Unknown',
                'description': f'Error reading manifest info: {e}',
                'url': ''
            }
    
    def _load_config(self) -> Dict[str, any]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_config(self, config: Dict[str, any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save config: {e}")
    
    def import_manifest_from_url(self, name: str, url: str, description: str = "", verify_checksums: bool = True) -> Tuple[bool, str]:
        """Import a manifest from an online URL"""
        import urllib.request
        
        try:
            # Validate inputs
            if not name or not name.replace('_', '').replace('-', '').isalnum():
                return False, "Manifest name must contain only letters, numbers, hyphens, and underscores"
            
            if not url.strip():
                return False, "URL cannot be empty"
            
            # Check if manifest with this name already exists
            manifest_file = self.custom_manifests_dir / f"{name}.json"
            if manifest_file.exists():
                return False, f"Manifest '{name}' already exists"
            
            # Download and validate the manifest
            if url.startswith('file://'):
                # Handle local file URLs
                file_path = url[7:]  # Remove 'file://' prefix
                if not os.path.exists(file_path):
                    return False, f"Local file not found: {file_path}"
                
                with open(file_path, 'r') as f:
                    manifest_content = f.read()
                    
            elif url.startswith(('http://', 'https://')):
                # Handle web URLs
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'lv_linux_learn/2.1.0')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    manifest_content = response.read().decode('utf-8')
            else:
                return False, "URL must start with http://, https://, or file://"
            
            # Parse and validate JSON
            try:
                manifest_data = json.loads(manifest_content)
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON format: {e}"
            
            # Basic validation
            if 'scripts' not in manifest_data and 'version' not in manifest_data:
                return False, "Does not appear to be a valid manifest file (missing 'scripts' or 'version' field)"
            
            # Save the original manifest directly - this allows the application to load it properly
            # Add metadata to identify it as imported
            manifest_data['_imported_metadata'] = {
                'name': name,
                'description': description or f"Imported from {url}",
                'imported_from': url,
                'imported_at': datetime.now().isoformat(),
                'type': 'imported_url',
                'verify_checksums': verify_checksums
            }
            
            # Also store verify_checksums at root level for consistency
            manifest_data['verify_checksums'] = verify_checksums
            
            # Save the manifest in the format expected by the application
            with open(manifest_file, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            return True, f"Successfully imported manifest '{name}' from {url}"
            
        except urllib.error.URLError as e:
            return False, f"Failed to download manifest: {e.reason}"
        except Exception as e:
            return False, f"Failed to import manifest: {str(e)}"
    
    def update_manifest_metadata(self, old_name: str, new_name: str, new_description: str, new_url: str = None, verify_checksums: bool = True) -> Tuple[bool, str]:
        """Update manifest metadata (name and description)"""
        try:
            # Check for directory-based manifest
            old_manifest_dir = self.custom_manifests_dir / old_name
            old_manifest_file = old_manifest_dir / "manifest.json"
            
            # Check for direct JSON file (imported URL)
            old_direct_file = self.custom_manifests_dir / f"{old_name}.json"
            
            if old_manifest_file.exists():
                # Directory-based manifest
                manifest_path = old_manifest_file
                is_directory_based = True
            elif old_direct_file.exists():
                # Direct JSON file manifest
                manifest_path = old_direct_file
                is_directory_based = False
            else:
                return False, f"Manifest '{old_name}' not found"
            
            # Load current manifest
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            # Check if name changed and new name already exists
            if old_name != new_name:
                if is_directory_based:
                    new_manifest_dir = self.custom_manifests_dir / new_name
                    if new_manifest_dir.exists():
                        return False, f"Manifest '{new_name}' already exists"
                else:
                    new_direct_file = self.custom_manifests_dir / f"{new_name}.json"
                    if new_direct_file.exists():
                        return False, f"Manifest '{new_name}' already exists"
            
            # Update metadata based on manifest type
            if is_directory_based:
                # Directory-based manifest
                manifest_data['repository_description'] = new_description
                manifest_data['verify_checksums'] = verify_checksums
                
                # If name changed, rename directory and files
                if old_name != new_name:
                    new_manifest_dir = self.custom_manifests_dir / new_name
                    new_scripts_dir = self.custom_scripts_dir / new_name
                    
                    # Rename directories
                    old_manifest_dir.rename(new_manifest_dir)
                    
                    # Rename scripts directory if it exists (backward compatibility)
                    # Note: v2.1.1+ doesn't create this, but older versions did
                    if (self.custom_scripts_dir / old_name).exists():
                        (self.custom_scripts_dir / old_name).rename(new_scripts_dir)
                    
                    # Update manifest file path
                    manifest_path = new_manifest_dir / "manifest.json"
                
                # Save updated manifest
                with open(manifest_path, 'w') as f:
                    json.dump(manifest_data, f, indent=2)
                
            else:
                # Imported URL manifest
                imported_metadata = manifest_data.get('_imported_metadata', {})
                imported_metadata['name'] = new_name
                imported_metadata['description'] = new_description
                imported_metadata['verify_checksums'] = verify_checksums
                manifest_data['_imported_metadata'] = imported_metadata
                
                # Also update root level verify_checksums for consistency
                manifest_data['verify_checksums'] = verify_checksums
                
                # Update URL if provided
                if new_url:
                    imported_metadata['imported_from'] = new_url
                
                # If name changed, rename file
                if old_name != new_name:
                    new_direct_file = self.custom_manifests_dir / f"{new_name}.json"
                    
                    # Save to new location
                    with open(new_direct_file, 'w') as f:
                        json.dump(manifest_data, f, indent=2)
                    
                    # Remove old file
                    old_direct_file.unlink()
                    
                    # Update active manifest URL if this is the current manifest
                    config = self._load_config()
                    current_url = config.get('custom_manifest_url', '')
                    if current_url == f"file://{old_direct_file}":
                        config['custom_manifest_url'] = f"file://{new_direct_file}"
                        self._save_config(config)
                else:
                    # Save updated manifest
                    with open(manifest_path, 'w') as f:
                        json.dump(manifest_data, f, indent=2)
            
            return True, f"Successfully updated manifest '{new_name}'"
            
        except Exception as e:
            return False, f"Failed to update manifest: {str(e)}"