"""
Manifest Module - Consolidated manifest operations
Combines manifest_loader + manifest_service + custom_manifest
Handles fetching, parsing, loading, and creating manifest files
"""

import json
import os
import time
import hashlib
import shutil
import tempfile
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from urllib.request import urlopen

try:
    from lib import config as C
except ImportError:
    C = None

try:
    from lib.repository import ScriptRepository
except ImportError:
    ScriptRepository = None


# ============================================================================
# MANIFEST LOADING
# ============================================================================

class ManifestLoader:
    """Handles fetching and loading scripts from manifest.json files"""
    
    @staticmethod
    def fetch_manifest(terminal_widget=None, repository=None) -> list[tuple[Path, str]]:
        """
        Fetch manifest.json from configured repository/repositories
        Returns list of (Path, source_name) tuples for all active manifests
        
        Args:
            terminal_widget: Optional terminal widget to send output to
            repository: Optional repository instance for custom configuration
            
        Returns:
            List of tuples containing (manifest_path, source_name) for each loaded manifest
        """
        manifests_to_load = []
        
        # Determine default manifest URL
        default_url = C.DEFAULT_MANIFEST_URL if C else "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
        manifest_url = os.environ.get('CUSTOM_MANIFEST_URL', default_url)
        
        # Ensure cache directory exists FIRST
        cache_dir = C.CONFIG_DIR if C else Path.home() / '.lv_linux_learn'
        cache_dir.mkdir(exist_ok=True)
        
        # Check repository config
        if repository:
            try:
                config = repository.load_config()
                
                # Check if public repository is enabled
                if config.get('use_public_repository', True):
                    manifests_to_load.append((manifest_url, 'Public Repository'))
                
                # Check for custom manifest
                custom_url = config.get('custom_manifest_url', '')
                if custom_url:
                    # Validate that local files actually exist before trying to load
                    if custom_url.startswith('file://'):
                        local_path = custom_url.replace('file://', '')
                        if not os.path.exists(local_path):
                            _terminal_output(terminal_widget, f"[!] Custom manifest not found: {local_path}")
                            _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                            # Clear the invalid configuration
                            config['custom_manifest_url'] = ''
                            config['custom_manifest_name'] = ''
                            if repository:
                                repository.save_config(config)
                        else:
                            custom_name = config.get('custom_manifest_name', 'Custom Repository')
                            manifests_to_load.append((custom_url, custom_name))
                    elif os.path.isfile(custom_url):
                        # Direct path without file:// prefix
                        if not os.path.exists(custom_url):
                            _terminal_output(terminal_widget, f"[!] Custom manifest not found: {custom_url}")
                            _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                            config['custom_manifest_url'] = ''
                            config['custom_manifest_name'] = ''
                            if repository:
                                repository.save_config(config)
                        else:
                            custom_name = config.get('custom_manifest_name', 'Custom Repository')
                            manifests_to_load.append((custom_url, custom_name))
                    else:
                        # Remote URL - add without validation (will fail later if unreachable)
                        custom_name = config.get('custom_manifest_name', 'Custom Repository')
                        manifests_to_load.append((custom_url, custom_name))
                
                # Load custom manifests from config['custom_manifests'] (new system)
                # Only load the active one, or all if none is active
                custom_manifests_config = config.get('custom_manifests', {})
                active_manifest = config.get('active_custom_manifest')
                has_custom_entries = bool(custom_manifests_config)

                # Track already-added manifests to avoid duplicates when we scan the directory
                seen_manifest_paths = set()

                if active_manifest and active_manifest in custom_manifests_config:
                    # Only load the active manifest
                    manifest_config = custom_manifests_config[active_manifest]
                    try:
                        manifest_data = manifest_config.get('manifest_data')
                        if manifest_data:
                            # Write manifest data to a temp file and add to load list
                            temp_manifest = cache_dir / f"temp_{active_manifest}_manifest.json"
                            with open(temp_manifest, 'w') as f:
                                json.dump(manifest_data, f, indent=2)
                            manifests_to_load.append((str(temp_manifest), active_manifest))
                            seen_manifest_paths.add(str(temp_manifest))
                            _terminal_output(terminal_widget, f"[*] Found active custom manifest: {active_manifest}")
                    except Exception as e:
                        _terminal_output(terminal_widget, f"[!] Error loading custom manifest '{active_manifest}': {e}")
                else:
                    # Load all available custom manifests if none is marked as active
                    for manifest_name, manifest_config in custom_manifests_config.items():
                        try:
                            manifest_data = manifest_config.get('manifest_data')
                            if manifest_data:
                                temp_manifest = cache_dir / f"temp_{manifest_name}_manifest.json"
                                with open(temp_manifest, 'w') as f:
                                    json.dump(manifest_data, f, indent=2)
                                manifests_to_load.append((str(temp_manifest), manifest_name))
                                seen_manifest_paths.add(str(temp_manifest))
                                _terminal_output(terminal_widget, f"[*] Found custom manifest: {manifest_name}")
                        except Exception as e:
                            _terminal_output(terminal_widget, f"[!] Error loading custom manifest '{manifest_name}': {e}")

                # CRITICAL: Scan for local repository manifests in custom_manifests directory
                # Always scan the directory so local repos work even if config lacks manifest_data
                custom_manifests_dir = cache_dir / 'custom_manifests'
                if custom_manifests_dir.exists():
                    for manifest_file in custom_manifests_dir.glob('*/manifest.json'):
                        repo_name = manifest_file.parent.name
                        local_manifest_url = f"file://{manifest_file}"
                        if str(manifest_file) in seen_manifest_paths:
                            continue
                        manifests_to_load.append((local_manifest_url, repo_name))
                        seen_manifest_paths.add(str(manifest_file))
                        if terminal_widget:
                            _terminal_output(terminal_widget, f"[*] Found local repository: {repo_name}")
                
            except Exception as e:
                print(f"[!] Error loading repository config: {e}")
        else:
            pass
        
        # If no manifests configured, raise error silently (expected when public repo disabled)
        if not manifests_to_load:
            error_msg = C.ERROR_NO_MANIFESTS if C else "No manifests configured. Enable public repository or add local repositories."
            raise Exception(error_msg)
        
        # Fetch and cache each manifest
        loaded_manifests = []
        
        for manifest_url, source_name in manifests_to_load:
            try:
                # Create cache filename based on source
                cache_filename = f"manifest_{source_name.lower().replace(' ', '_')}.json"
                cache_path = cache_dir / cache_filename
                
                # Try to load from cache first
                use_cache = False
                max_age = C.MANIFEST_CACHE_MAX_AGE if C else 3600
                
                if cache_path.exists():
                    age = time.time() - cache_path.stat().st_mtime
                    if age < max_age:
                        use_cache = True
                
                if not use_cache:
                    # Fetch from URL - handle both remote URLs and local file:// paths
                    if manifest_url.startswith('file://'):
                        # Local file path
                        local_path = manifest_url[7:]  # Remove 'file://' prefix
                        manifest_content = Path(local_path).read_text()
                    elif os.path.isfile(manifest_url):
                        # Direct file path (no file:// prefix)
                        manifest_content = Path(manifest_url).read_text()
                    else:
                        # Remote URL (http/https)
                        response = urlopen(manifest_url, timeout=10)
                        manifest_content = response.read().decode('utf-8')
                    
                    # Save to cache (no output message)
                    cache_path.write_text(manifest_content)
                
                loaded_manifests.append((cache_path, source_name))
                
            except Exception as e:
                _terminal_output(terminal_widget, f"[!] Failed to load manifest from {source_name}: {e}")
                continue
        
        if not loaded_manifests:
            error_msg = C.ERROR_MANIFEST_LOAD_FAILED if C else "Failed to load any manifests"
            raise Exception(error_msg)
        
        return loaded_manifests
    
    @staticmethod
    def load_scripts_from_manifest(
        terminal_widget=None,
        repository=None
    ) -> tuple[dict[str, list], dict[str, list], dict[str, list]]:
        """
        Load scripts dynamically from manifest.json files (supports multiple manifests)
        Returns: tuple of (scripts_dict, names_dict, descriptions_dict)
        """
        
        try:
            # Fetch all active manifests (returns list of (path, source_name) tuples)
            try:
                manifests = ManifestLoader.fetch_manifest(terminal_widget, repository)
            except Exception as e:
                # If no manifests are configured or fetch fails, return empty structures
                _terminal_output(terminal_widget, f"[!] Manifest load failed: {e}")
                return ({}, {}, {}, {})
            
            # Initialize merged structures
            standard_cats = C.STANDARD_CATEGORIES if C else ['install', 'tools', 'exercises', 'uninstall']
            all_categories = set(standard_cats)
            scripts = {}
            names = {}
            descriptions = {}
            
            # Initialize repository for cache management
            repo = repository if repository else (ScriptRepository() if ScriptRepository else None)
            
            # Process each manifest
            total_scripts_all = 0
            total_cached_all = 0
            
            # Global script ID mapping for metadata building
            script_id_map = {}
            
            # Track script IDs to prevent duplicates
            seen_script_ids = set()
            
            for manifest_path, source_name in manifests:
                try:
                    with open(manifest_path, 'r') as f:
                        manifest_data = json.load(f)
                    
                    # Get manifest version and repository_url (for internal use, no output)
                    manifest_version = manifest_data.get('version', 'unknown')
                    repository_url = manifest_data.get('repository_url', '')
                    
                    # Load scripts from manifest - handle both flat and nested structures
                    manifest_scripts_raw = manifest_data.get('scripts', [])
                    manifest_scripts = []
                    
                    # Check if scripts is a dict (nested by category) or list (flat)
                    if isinstance(manifest_scripts_raw, dict):
                        # Nested structure: {"category": [scripts]}
                        _terminal_output(terminal_widget, f"[*] Processing nested manifest structure")
                        for cat, cat_scripts in manifest_scripts_raw.items():
                            if isinstance(cat_scripts, list):
                                _terminal_output(terminal_widget, f"[*] Processing {len(cat_scripts)} scripts in category '{cat}'")
                                for script in cat_scripts:
                                    # CRITICAL: In nested structure, the category key is authoritative
                                    # Always set category from the dict key, overriding any field value
                                    script['category'] = cat
                                    manifest_scripts.append(script)
                    else:
                        # Flat structure: [scripts]
                        manifest_scripts = manifest_scripts_raw
                    
                    total_scripts = len(manifest_scripts)
                    cached_count = 0
                    
                    _terminal_output(terminal_widget, f"[*] Found {total_scripts} scripts in manifest")
                    
                    for script_entry in manifest_scripts:
                        category = script_entry.get('category', 'install')
                        
                        # Add category if not seen before
                        if category not in all_categories:
                            all_categories.add(category)
                        
                        # Initialize category if needed
                        if category not in scripts:
                            scripts[category] = []
                            names[category] = []
                            descriptions[category] = []
                        
                        # Get script details
                        script_id = script_entry.get('id', '')
                        script_name = script_entry.get('name', '')
                        file_name = script_entry.get('file_name', '')
                        relative_path = script_entry.get('relative_path', '')
                        download_url = script_entry.get('download_url', '')
                        description = script_entry.get('description', 'No description available')
                        
                        # Skip duplicates - check if script ID already processed
                        if script_id and script_id in seen_script_ids:
                            _terminal_output(terminal_widget, f"[*] Skipping duplicate: {script_name} (ID: {script_id})")
                            continue
                        
                        # Mark as seen
                        if script_id:
                            seen_script_ids.add(script_id)
                        
                        # Determine script path based on source type
                        script_path = relative_path
                        is_cached = False
                        is_local = False
                        
                        # Check if this is a local file:// URL (from local repository)
                        if download_url and download_url.startswith('file://'):
                            # Local file - use the file path directly
                            script_path = download_url.replace('file://', '')
                            is_local = True
                            _terminal_output(terminal_widget, f"[*] Local script: {script_name} -> {script_path}")
                        elif repo and script_id:
                            # Check if script is cached (online repositories)
                            cached_path = repo.get_cached_script_path(script_id)
                            if cached_path and os.path.exists(cached_path):
                                script_path = cached_path
                                is_cached = True
                                cached_count += 1
                                pass  # removed debug log
                            else:
                                pass  # removed debug log
                        
                        # Build display name with source tag
                        base_name = script_name
                        
                        # Add source identifier to name
                        if is_local:
                            display_name = f"{base_name} [Local: {source_name}]"
                        elif source_name == 'Public Repository':
                            display_name = f"{base_name} [Public Repository]"
                        else:
                            display_name = f"{base_name} [Custom: {source_name}]"
                        
                        # Add to lists
                        scripts[category].append(script_path)
                        names[category].append(display_name)
                        descriptions[category].append(description)
                        
                        # Store in global mapping for metadata building
                        script_id_map[(category, script_path)] = (script_id, source_name)
                    
                    total_scripts_all += total_scripts
                    total_cached_all += cached_count
                    
                    # Concise per-source summary
                    _terminal_output(terminal_widget, f"[✓] {source_name}: {total_scripts} scripts ({cached_count} cached)")
                    pass  # removed debug log
                    
                except Exception as e:
                    _terminal_output(terminal_widget, f"[!] {source_name}: Failed - {e}")
                    continue
            
            # Ensure all standard categories exist even if empty
            for cat in standard_cats:
                if cat not in scripts:
                    scripts[cat] = []
                    names[cat] = []
                    descriptions[cat] = []
            
            # Display concise summary
            categories_summary = ", ".join([f"{cat}:{len(scripts[cat])}" for cat in sorted(scripts.keys()) if len(scripts[cat]) > 0])
            _terminal_output(terminal_widget, f"\n[✓] Loaded {total_scripts_all} scripts from {len(manifests)} source(s) - {categories_summary}")
            
            return scripts, names, descriptions, script_id_map
            
        except Exception as e:
            # Suppress "No manifests configured" error - it's expected when public repo is disabled
            error_str = str(e)
            if "No manifests configured" not in error_str:
                _terminal_output(terminal_widget, f"[!] Error loading manifests: {e}")
            # Return empty structures
            default_categories = C.STANDARD_CATEGORIES if C else ['install', 'tools', 'exercises', 'uninstall']
            scripts = {cat: [] for cat in default_categories}
            names = {cat: [] for cat in default_categories}
            descriptions = {cat: [] for cat in default_categories}
            return scripts, names, descriptions, {}


# ============================================================================
# MANIFEST MANAGEMENT
# ============================================================================

class ManifestManager:
    """Manages local repository manifests with AI-powered categorization"""
    
    def __init__(self, manifest_path: str):
        """Initialize manifest manager"""
        self.manifest_path = Path(manifest_path)
        self.manifest_data = None
        self.load_manifest()
    
    def load_manifest(self) -> bool:
        """Load manifest from file"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r') as f:
                    self.manifest_data = json.load(f)
                return True
            return False
        except Exception as e:
            print(f"Error loading manifest: {e}")
            return False
    
    def save_manifest(self) -> bool:
        """Save manifest to file with proper error handling and directory creation"""
        try:
            # Ensure parent directory exists
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we have write permissions
            if self.manifest_path.exists() and not os.access(self.manifest_path, os.W_OK):
                print(f"Error: No write permission for {self.manifest_path}")
                return False
            
            # Check if we can write to parent directory
            if not os.access(self.manifest_path.parent, os.W_OK):
                print(f"Error: No write permission for directory {self.manifest_path.parent}")
                return False
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.manifest_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(self.manifest_data, f, indent=2)
            
            # Rename temp file to actual manifest (atomic)
            temp_path.replace(self.manifest_path)
            return True
        except PermissionError as e:
            print(f"Permission denied saving manifest {self.manifest_path}: {e}")
            return False
        except Exception as e:
            print(f"Error saving manifest {self.manifest_path}: {e}")
            return False
    
    def update_script_from_ai_analysis(self, script_id: str, analysis: Dict) -> bool:
        """Update script metadata from AI analysis results"""
        if not self.manifest_data:
            return False
        
        scripts = self.manifest_data.get('scripts', {})
        
        if not isinstance(scripts, dict):
            print(f"Error: Manifest scripts is not a dict, got {type(scripts)}")
            return False
        
        # Search for script in all categories
        found = False
        for category, category_scripts in scripts.items():
            if not isinstance(category_scripts, list):
                print(f"Warning: Scripts in category '{category}' is not a list, skipping")
                continue
                
            for script in category_scripts:
                if script.get('id') == script_id:
                    found = True
                    # Update from analysis
                    if 'category' in analysis and analysis['category'] != category:
                        # Need to move to different category
                        new_cat = analysis['category']
                        if new_cat not in scripts:
                            scripts[new_cat] = []
                        
                        # Ensure new category is a list
                        if not isinstance(scripts[new_cat], list):
                            scripts[new_cat] = []
                        
                        # Remove from old category
                        category_scripts.remove(script)
                        
                        # Add to new category with updated info
                        script['category'] = new_cat
                        if 'description' in analysis:
                            script['description'] = analysis['description']
                        scripts[new_cat].append(script)
                    else:
                        # Just update description
                        if 'description' in analysis:
                            script['description'] = analysis['description']
                    
                    # Save after updating
                    if self.save_manifest():
                        return True
                    else:
                        print(f"Failed to save manifest after updating script {script_id}")
                        return False
        
        if not found:
            print(f"Script with ID '{script_id}' not found in manifest")
        
        return False
    
    def get_all_scripts(self) -> List[Dict]:
        """Get all scripts from manifest as flat list"""
        if not self.manifest_data:
            return []
        
        all_scripts = []
        scripts = self.manifest_data.get('scripts', {})
        
        for category, category_scripts in scripts.items():
            if isinstance(category_scripts, list):
                for script in category_scripts:
                    script['category'] = category
                    all_scripts.append(script)
        
        return all_scripts


def get_local_repository_manifests() -> List[Tuple[str, str]]:
    """Get list of local repository manifests from configuration"""
    try:
        config_path = Path.home() / '.lv_linux_learn' / 'config.json'
        if not config_path.exists():
            return []
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        manifests = []
        custom_manifests = config.get('custom_manifests', {})
        
        for name, manifest_config in custom_manifests.items():
            url = manifest_config.get('url', '')
            if url.startswith('file://'):
                local_path = url[7:]
                if os.path.exists(local_path):
                    manifests.append((name, local_path))
        
        return manifests
        
    except Exception as e:
        print(f"Error getting local manifests: {e}")
        return []


# ============================================================================
# CUSTOM MANIFEST CREATION
# ============================================================================

class ScriptScanner:
    """Scans directories for executable shell scripts and extracts metadata"""
    
    def __init__(self):
        self.script_extensions = ['.sh', '.bash']
        self.executable_patterns = ['#!/bin/bash', '#!/bin/sh', '#!/usr/bin/env bash']
    
    def is_executable_script(self, file_path: Path) -> bool:
        """Check if file is a shell script"""
        if not file_path.is_file():
            return False
        
        if file_path.suffix not in self.script_extensions:
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                return any(pattern in first_line for pattern in self.executable_patterns)
        except Exception:
            return False
    
    def extract_script_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract metadata from script headers"""
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
            
            for line in lines[:50]:  # Check first 50 lines
                stripped = line.strip()
                
                # Start of description
                if stripped.startswith('# Description:'):
                    desc_text = stripped.replace('# Description:', '').strip()
                    if desc_text:
                        description_lines.append(desc_text)
                    in_description = True
                    continue
                
                # Continuation of multi-line description
                if in_description:
                    if stripped.startswith('#') and not stripped.startswith('##'):
                        # Remove leading # and whitespace
                        desc_line = stripped.lstrip('#').strip()
                        if desc_line:
                            description_lines.append(desc_line)
                        else:
                            break  # Empty comment line ends description
                    else:
                        break  # Non-comment line ends description
                
                # Version
                if 'Version:' in line:
                    match = re.search(r'Version:\s*([^\s]+)', line)
                    if match:
                        metadata['version'] = match.group(1)
                
                # Category
                if 'Category:' in line:
                    match = re.search(r'Category:\s*([^\s]+)', line)
                    if match:
                        metadata['category'] = match.group(1).lower()
            
            if description_lines:
                metadata['description'] = ' '.join(description_lines)
            
        except Exception:
            pass
        
        return metadata
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Tuple[Path, Dict]]:
        """Scan directory for scripts and return list of (path, metadata) tuples"""
        scripts = []
        
        if recursive:
            pattern = '**/*'
        else:
            pattern = '*'
        
        for item in directory.glob(pattern):
            if self.is_executable_script(item):
                metadata = self.extract_script_metadata(item)
                scripts.append((item, metadata))
        
        return scripts


class CustomManifestCreator:
    """Creates custom manifest.json files from directory scans"""
    
    def __init__(self):
        self.scanner = ScriptScanner()
    
    def create_manifest(
        self,
        manifest_name: str,
        directories: list,
        description: str = "",
        recursive: bool = True,
        verify_checksums: bool = True
    ) -> tuple:
        """
        Create a manifest.json file from scripts in directories.
        
        Args:
            manifest_name: Name for the manifest
            directories: List of directory paths (strings or Path objects)
            description: Description of the manifest
            recursive: Whether to scan recursively
            verify_checksums: Whether to verify checksums
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Build manifest structure
            manifest = {
                "name": manifest_name,
                "version": "1.0.0",
                "description": description or f"Custom script collection: {manifest_name}",
                "created": datetime.now().isoformat(),
                "scripts": {}
            }
            
            total_scripts = 0
            
            # Scan all directories
            for directory in directories:
                # Convert string to Path if necessary
                if isinstance(directory, str):
                    dir_path = Path(directory)
                else:
                    dir_path = directory
                
                if not dir_path.exists():
                    raise Exception(f"Directory does not exist: {dir_path}")
                
                if not dir_path.is_dir():
                    raise Exception(f"Not a directory: {dir_path}")
                
                # Scan for scripts
                scripts = self.scanner.scan_directory(dir_path, recursive)
                
                if not scripts:
                    continue
                
                # Organize by category
                for script_path, metadata in scripts:
                    category = metadata.get('category', 'custom')
                    
                    if category not in manifest['scripts']:
                        manifest['scripts'][category] = []
                    
                    # Generate script ID
                    script_id = self._generate_script_id(str(script_path))
                    
                    # Calculate checksum if needed
                    checksum = None
                    if verify_checksums:
                        checksum = self._calculate_checksum(script_path)
                    
                    script_entry = {
                        "id": script_id,
                        "name": metadata.get('name', script_path.stem),
                        "file_name": str(script_path),
                        "description": metadata.get('description', ''),
                        "version": metadata.get('version', '1.0.0'),
                        "category": category,
                    }
                    
                    if checksum:
                        script_entry["sha256"] = checksum
                    
                    manifest['scripts'][category].append(script_entry)
                    total_scripts += 1
            
            if total_scripts == 0:
                raise Exception("No shell scripts found in any of the provided directories")
            
            # Save manifest to config
            config_dir = Path.home() / '.lv_linux_learn'
            config_dir.mkdir(parents=True, exist_ok=True)

            # Persist manifest.json under ~/.lv_linux_learn/custom_manifests/<name>/manifest.json
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', manifest_name.strip()) or "custom_manifest"
            manifest_dir = config_dir / 'custom_manifests' / safe_name
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_file = manifest_dir / 'manifest.json'
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            config_file = config_dir / 'config.json'
            config = {}
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except Exception:
                    pass
            
            if 'custom_manifests' not in config:
                config['custom_manifests'] = {}
            
            config['custom_manifests'][manifest_name] = {
                'type': 'local',
                'directories': [str(d) for d in directories],
                'verify_checksums': verify_checksums,
                'created': datetime.now().isoformat(),
                'manifest_path': str(manifest_file),
                'manifest_data': manifest
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            message = f"Created manifest '{manifest_name}' with {total_scripts} scripts"
            return (True, message)
            
        except Exception as e:
            error_msg = str(e)
            return (False, error_msg)
    
    def import_manifest_from_url(
        self,
        manifest_name: str,
        url: str,
        description: str = "",
        verify_checksums: bool = True
    ) -> tuple:
        """
        Import a manifest from a URL.
        
        Args:
            manifest_name: Name for the manifest
            url: URL to the manifest (http://, https://, or file://)
            description: Description of the manifest
            verify_checksums: Whether to verify checksums
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Fetch manifest from URL
            if url.startswith('file://'):
                manifest_path = Path(url[7:])
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
            else:
                import urllib.request
                with urllib.request.urlopen(url) as response:
                    manifest_data = json.load(response)
            
            # Validate manifest structure
            if not isinstance(manifest_data, dict):
                raise Exception("Invalid manifest: must be a JSON object")
            
            if 'scripts' not in manifest_data:
                raise Exception("Invalid manifest: missing 'scripts' key")
            
            # Save to config
            config_dir = Path.home() / '.lv_linux_learn'
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = config_dir / 'config.json'
            config = {}
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                except Exception:
                    pass
            
            if 'custom_manifests' not in config:
                config['custom_manifests'] = {}
            
            config['custom_manifests'][manifest_name] = {
                'type': 'remote',
                'url': url,
                'description': description,
                'verify_checksums': verify_checksums,
                'created': datetime.now().isoformat(),
                'manifest_data': manifest_data
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            message = f"Imported manifest '{manifest_name}' from {url}"
            return (True, message)
            
        except Exception as e:
            error_msg = str(e)
            return (False, error_msg)
    
    def switch_to_custom_manifest(self, manifest_name: str) -> tuple:
        """
        Switch the active custom manifest.
        
        Args:
            manifest_name: Name of the manifest to activate
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            config_dir = Path.home() / '.lv_linux_learn'
            config_file = config_dir / 'config.json'
            
            if not config_file.exists():
                raise Exception("No configuration file found")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'custom_manifests' not in config or manifest_name not in config['custom_manifests']:
                raise Exception(f"Manifest '{manifest_name}' not found")
            
            # Set as active
            config['active_custom_manifest'] = manifest_name
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            message = f"Switched to manifest '{manifest_name}'"
            return (True, message)
            
        except Exception as e:
            error_msg = str(e)
            return (False, error_msg)
    
    def delete_custom_manifest(self, manifest_name: str) -> tuple:
        """
        Delete a custom manifest.
        
        Args:
            manifest_name: Name of the manifest to delete
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            config_dir = Path.home() / '.lv_linux_learn'
            config_file = config_dir / 'config.json'
            
            if not config_file.exists():
                raise Exception("No configuration file found")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'custom_manifests' not in config or manifest_name not in config['custom_manifests']:
                raise Exception(f"Manifest '{manifest_name}' not found")

            manifest_entry = config['custom_manifests'][manifest_name]
            manifest_path = manifest_entry.get('manifest_path')
            
            # Comprehensive cleanup of all related files
            try:
                # 1. Remove persisted manifest directory/file
                if manifest_path:
                    mpath = Path(manifest_path)
                    if mpath.exists():
                        # If manifest is inside custom_manifests/<name>, remove directory
                        if mpath.name == 'manifest.json' and mpath.parent.name:
                            parent_dir = mpath.parent
                            if parent_dir.exists() and str(parent_dir).startswith(str(Path.home() / '.lv_linux_learn' / 'custom_manifests')):
                                shutil.rmtree(parent_dir, ignore_errors=True)
                        else:
                            mpath.unlink(missing_ok=True)
                
                # 2. Remove cached manifest files (manifest_<name>.json and temp_<name>_manifest.json)
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', manifest_name.lower().strip())
                cache_files = [
                    config_dir / f"manifest_{safe_name}.json",
                    config_dir / f"temp_{manifest_name}_manifest.json",
                    config_dir / f"manifest_{manifest_name.lower().replace(' ', '_')}.json"
                ]
                for cache_file in cache_files:
                    cache_file.unlink(missing_ok=True)
                
                # 3. Remove scripts from cache if they came from this manifest
                # Scripts are cached under ~/.lv_linux_learn/script_cache/<category>/<script_id>
                # We'll remove based on manifest source type
                cache_root = config_dir / 'script_cache'
                if cache_root.exists() and manifest_entry.get('type') in ('local', 'remote'):
                    # For local manifests, remove scripts from all categories that came from this source
                    # This is a best-effort cleanup - ideally scripts would have source metadata
                    # For now, users can manually clear cache if needed via the app UI
                    pass
                    
            except Exception as e:
                # Non-fatal; we still remove config entry
                print(f"Warning: Cleanup for manifest '{manifest_name}' had issues: {e}")
            
            del config['custom_manifests'][manifest_name]
            
            # Clear active if it was the deleted one
            if config.get('active_custom_manifest') == manifest_name:
                config['active_custom_manifest'] = None
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            message = f"Deleted manifest '{manifest_name}'"
            return (True, message)
            
        except Exception as e:
            error_msg = str(e)
            return (False, error_msg)
    
    def update_manifest_metadata(
        self,
        manifest_name: str,
        description: str = None,
        verify_checksums: bool = None
    ) -> tuple:
        """
        Update metadata for a custom manifest.
        
        Args:
            manifest_name: Name of the manifest to update
            description: New description (optional)
            verify_checksums: New checksum setting (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            config_dir = Path.home() / '.lv_linux_learn'
            config_file = config_dir / 'config.json'
            
            if not config_file.exists():
                raise Exception("No configuration file found")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'custom_manifests' not in config or manifest_name not in config['custom_manifests']:
                raise Exception(f"Manifest '{manifest_name}' not found")
            
            manifest = config['custom_manifests'][manifest_name]
            
            if description is not None:
                manifest['description'] = description
            
            if verify_checksums is not None:
                manifest['verify_checksums'] = verify_checksums
            
            manifest['updated'] = datetime.now().isoformat()
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            message = f"Updated manifest '{manifest_name}'"
            return (True, message)
            
        except Exception as e:
            error_msg = str(e)
            return (False, error_msg)
    
    def list_custom_manifests(self) -> List[Dict[str, any]]:
        """List all created custom manifests"""
        manifests = []
        
        try:
            config_path = Path.home() / '.lv_linux_learn' / 'config.json'
            if not config_path.exists():
                return manifests
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            custom_manifests_config = config.get('custom_manifests', {})
            
            for name, manifest_config in custom_manifests_config.items():
                url = manifest_config.get('url', '')
                manifest_data = manifest_config.get('manifest_data')

                # Fallback: if no manifest_data in config but manifest_path exists, load it
                if not manifest_data:
                    manifest_path = manifest_config.get('manifest_path')
                    if manifest_path and Path(manifest_path).exists():
                        try:
                            with open(manifest_path, 'r') as mf:
                                manifest_data = json.load(mf)
                        except Exception:
                            manifest_data = None

                # Derive display fields
                description = manifest_config.get('description', '')
                version = '1.0.0'
                created = manifest_config.get('created', '')
                total_scripts = 0
                categories = []

                if manifest_data:
                    description = manifest_data.get('description', description)
                    version = manifest_data.get('version', version)
                    created = manifest_data.get('created', created)

                    scripts_section = manifest_data.get('scripts', {})
                    if isinstance(scripts_section, dict):
                        for cat, cat_scripts in scripts_section.items():
                            if isinstance(cat_scripts, list):
                                categories.append(cat)
                                total_scripts += len(cat_scripts)
                    elif isinstance(scripts_section, list):
                        total_scripts = len(scripts_section)
                        categories = sorted({s.get('category', 'custom') for s in scripts_section if isinstance(s, dict)})

                manifests.append({
                    'name': name,
                    'url': url,
                    'verify_checksums': manifest_config.get('verify_checksums', True),
                    'type': 'remote' if url.startswith('http') else 'local',
                    'description': description,
                    'version': version,
                    'created': created,
                    'total_scripts': total_scripts,
                    'categories': categories or []
                })
            
            return manifests
            
        except Exception as e:
            print(f"Error listing manifests: {e}")
            return []
    
    def _generate_script_id(self, rel_path: str) -> str:
        """Generate unique script ID from relative path"""
        # Use path hash for consistency
        path_hash = hashlib.md5(rel_path.encode()).hexdigest()[:8]
        # Combine with sanitized filename
        clean_name = re.sub(r'[^a-z0-9_]', '_', rel_path.lower())
        return f"{clean_name}_{path_hash}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _terminal_output(terminal_widget, msg: str):
    """Helper function to output to terminal or stdout - only errors displayed to terminal"""
    # Only show error messages in terminal to avoid cluttering output during background refreshes
    # Status/info messages are logged but not displayed
    if msg.startswith("[!]") or msg.startswith("[✗]"):
        if terminal_widget:
            terminal_widget.feed(f"{msg}\r\n".encode())
        else:
            print(msg)
    # All other messages silently logged (could be logged to file if needed)


# ============================================================================
# BACKWARD COMPATIBILITY - Keep old function names for existing code
# ============================================================================

def fetch_manifest(terminal_widget=None, repository=None):
    """Backward compatibility wrapper"""
    return ManifestLoader.fetch_manifest(terminal_widget, repository)

def load_scripts_from_manifest(terminal_widget=None, repository=None):
    """Backward compatibility wrapper"""
    return ManifestLoader.load_scripts_from_manifest(terminal_widget, repository)
