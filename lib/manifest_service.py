"""
Manifest Service Module - Consolidated manifest operations
Combines manifest_loader.py + manifest_manager.py + custom_manifest.py
Handles fetching, parsing, loading, and creating manifest files
"""

import json
import os
import time
import hashlib
import shutil
import tempfile
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from urllib.request import urlopen

try:
    from lib import config as C
except ImportError:
    C = None

try:
    from lib.repository_service import ScriptRepository
except ImportError:
    ScriptRepository = None


# ============================================================================
# MANIFEST LOADING - from manifest_loader.py
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
        
        # Get repository configuration if available
        if repository and hasattr(repository, 'load_config'):
            try:
                config = repository.load_config()
                use_public_repo = config.get('use_public_repository', True)
                custom_manifest_url = config.get('custom_manifest_url', '')
                
                # Check for local repositories (file:// URLs)
                custom_manifests = config.get('custom_manifests', {})
                for manifest_name, manifest_config in custom_manifests.items():
                    manifest_url = manifest_config.get('url', '')
                    if manifest_url.startswith('file://'):
                        local_path = manifest_url[7:]  # Remove file:// prefix
                        if os.path.exists(local_path):
                            manifests_to_load.append((manifest_url, manifest_name))
                        else:
                            _terminal_output(terminal_widget, f"[!] Custom manifest not found: {local_path}")
                            _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                            # Remove invalid manifest
                            del custom_manifests[manifest_name]
                            config['custom_manifests'] = custom_manifests
                            repository.save_config(config)
                
                # Add public repository if enabled
                if use_public_repo:
                    # Get repository root - use local_repo_root or fallback to calculated path
                    if hasattr(repository, 'local_repo_root') and repository.local_repo_root:
                        repo_root = repository.local_repo_root
                    else:
                        repo_root = Path(__file__).parent.parent
                    manifest_path = repo_root / "manifest.json"
                    manifests_to_load.append((str(manifest_path), "Public Repository"))
                
                # Add legacy custom manifest URL if configured
                if custom_manifest_url and custom_manifest_url not in [m[0] for m in manifests_to_load]:
                    if custom_manifest_url.startswith('file://'):
                        if not os.path.exists(custom_manifest_url[7:]):
                            _terminal_output(terminal_widget, f"[!] Custom manifest not found: {custom_manifest_url}")
                            _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                            config['custom_manifest_url'] = ''
                            repository.save_config(config)
                        else:
                            manifests_to_load.append((custom_manifest_url, "Custom Manifest"))
                    else:
                        manifests_to_load.append((custom_manifest_url, "Custom Manifest"))
                
                # Track local repositories for display
                local_repos = [name for name, url in manifests_to_load if url[0].startswith('file://')]
                for repo_name in local_repos:
                    if hasattr(terminal_widget, 'feed'):
                        pass  # Silently track, don't output
                        
            except Exception as e:
                print(f"[!] Error loading repository config: {e}")
        else:
            # No repository instance - load default
            pass
        
        # If no manifests configured, raise error silently
        if not manifests_to_load:
            error_msg = C.ERROR_NO_MANIFESTS if C else "No manifests configured. Enable public repository or add local repositories."
            raise Exception(error_msg)
        
        return manifests_to_load
    
    @staticmethod
    def load_scripts_from_manifest(terminal_widget=None, repository=None):
        """
        Load scripts from configured manifest(s)
        
        Returns:
            Tuple of (scripts_dict, names_dict, descriptions_dict, script_id_map)
        """
        try:
            # Fetch manifests
            manifests_to_load = ManifestLoader.fetch_manifest(terminal_widget, repository)
            
            # Load and parse each manifest
            loaded_manifests = []
            
            for manifest_url, source_name in manifests_to_load:
                try:
                    manifest_data = ManifestLoader._load_manifest_file(manifest_url, source_name, terminal_widget, repository)
                    if manifest_data:
                        loaded_manifests.append((manifest_data, source_name))
                except Exception as e:
                    _terminal_output(terminal_widget, f"[!] Failed to load manifest from {source_name}: {e}")
                    continue
            
            # Process all manifests into unified structure
            return ManifestLoader._process_manifests(loaded_manifests, terminal_widget, repository)
            
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
    
    @staticmethod
    def _load_manifest_file(manifest_url: str, source_name: str, terminal_widget, repository):
        """Load a single manifest file from URL or local path"""
        if manifest_url.startswith('file://'):
            # Local file
            local_path = manifest_url[7:]
            with open(local_path, 'r') as f:
                return json.load(f)
        elif manifest_url.startswith('http://') or manifest_url.startswith('https://'):
            # Remote URL
            cache_dir = repository.script_cache_dir if repository else Path.home() / '.lv_linux_learn' / 'script_cache'
            cache_dir.mkdir(parents=True, exist_ok=True)
            cached_manifest = cache_dir / f"manifest_{source_name.replace(' ', '_').lower()}.json"
            
            # Fetch from URL
            response = urlopen(manifest_url, timeout=10)
            data = response.read().decode('utf-8')
            manifest_data = json.loads(data)
            
            # Cache it
            with open(cached_manifest, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            return manifest_data
        else:
            # Assume local file path
            with open(manifest_url, 'r') as f:
                return json.load(f)
    
    @staticmethod
    def _process_manifests(loaded_manifests: list, terminal_widget, repository):
        """Process loaded manifests into categorized script dictionaries"""
        default_categories = C.STANDARD_CATEGORIES if C else ['install', 'tools', 'exercises', 'uninstall']
        scripts_dict = {cat: [] for cat in default_categories}
        names_dict = {cat: [] for cat in default_categories}
        descriptions_dict = {cat: [] for cat in default_categories}
        script_id_map = {}
        
        total_scripts_all = 0
        categories_found = set()
        
        for manifest_data, source_name in loaded_manifests:
            try:
                manifest_scripts = manifest_data.get('scripts', {})
                total_scripts = 0
                cached_count = 0
                
                # Handle both nested (by category) and flat structures
                if isinstance(manifest_scripts, dict):
                    # Nested structure
                    for cat, cat_scripts in manifest_scripts.items():
                        if isinstance(cat_scripts, list):
                            total_scripts += len(cat_scripts)
                            categories_found.add(cat)
                            
                            # Ensure category exists in dictionaries
                            if cat not in scripts_dict:
                                scripts_dict[cat] = []
                                names_dict[cat] = []
                                descriptions_dict[cat] = []
                            
                            for script in cat_scripts:
                                script_id = script.get('id')
                                script_name = script.get('name', 'Unknown')
                                script_path = script.get('file_name', '')
                                
                                # Check if cached
                                if repository and hasattr(repository, 'is_script_cached'):
                                    if repository.is_script_cached(script_id, cat, script_path):
                                        cached_count += 1
                                
                                # Track script ID for quick lookup
                                if script_id and script_id not in script_id_map:
                                    script_id_map[script_id] = {
                                        'name': script_name,
                                        'category': cat,
                                        'source': source_name,
                                        'path': script_path
                                    }
                                
                                # Add to category lists
                                scripts_dict[cat].append(script_path)
                                names_dict[cat].append(script_name)
                                descriptions_dict[cat].append(script.get('description', ''))
                else:
                    # Flat structure - assign default category
                    default_cat = 'tools'
                    if isinstance(manifest_scripts, list):
                        total_scripts = len(manifest_scripts)
                        for script in manifest_scripts:
                            cat = script.get('category', default_cat)
                            categories_found.add(cat)
                            
                            # Ensure category exists
                            if cat not in scripts_dict:
                                scripts_dict[cat] = []
                                names_dict[cat] = []
                                descriptions_dict[cat] = []
                            
                            script_id = script.get('id')
                            script_name = script.get('name', 'Unknown')
                            script_path = script.get('file_name', '')
                            
                            # Track script ID
                            if script_id and script_id not in script_id_map:
                                script_id_map[script_id] = {
                                    'name': script_name,
                                    'category': cat,
                                    'source': source_name,
                                    'path': script_path
                                }
                            
                            scripts_dict[cat].append(script_path)
                            names_dict[cat].append(script_name)
                            descriptions_dict[cat].append(script.get('description', ''))
                
                total_scripts_all += total_scripts
                
            except Exception as e:
                _terminal_output(terminal_widget, f"[!] {source_name}: Failed - {e}")
                continue
        
        categories_summary = f"{len(categories_found)} categories"
        
        return scripts_dict, names_dict, descriptions_dict, script_id_map


# ============================================================================
# MANIFEST MANAGEMENT - from manifest_manager.py
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
        """Save manifest to file"""
        try:
            with open(self.manifest_path, 'w') as f:
                json.dump(self.manifest_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving manifest: {e}")
            return False
    
    def update_script_from_ai_analysis(self, script_id: str, analysis: Dict) -> bool:
        """Update script metadata from AI analysis results"""
        if not self.manifest_data:
            return False
        
        scripts = self.manifest_data.get('scripts', {})
        
        # Search for script in all categories
        for category, category_scripts in scripts.items():
            if isinstance(category_scripts, list):
                for script in category_scripts:
                    if script.get('id') == script_id:
                        # Update from analysis
                        if 'category' in analysis and analysis['category'] != category:
                            # Need to move to different category
                            new_cat = analysis['category']
                            if new_cat not in scripts:
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
                        
                        return self.save_manifest()
        
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
# CUSTOM MANIFEST CREATION - from custom_manifest.py
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
        base_dir: Path,
        manifest_path: Path,
        manifest_name: str = "Custom Scripts",
        recursive: bool = True,
        organize_by_category: bool = True
    ) -> bool:
        """Create a manifest.json file from scripts in a directory"""
        try:
            # Scan for scripts
            scripts = self.scanner.scan_directory(base_dir, recursive)
            
            if not scripts:
                raise Exception("No shell scripts found in directory")
            
            # Build manifest structure
            manifest = {
                "name": manifest_name,
                "version": "1.0.0",
                "description": f"Custom script collection from {base_dir.name}",
                "created": datetime.now().isoformat(),
                "base_path": str(base_dir),
                "scripts": {}
            }
            
            if organize_by_category:
                # Organize by category
                for script_path, metadata in scripts:
                    category = metadata.get('category', 'custom')
                    
                    if category not in manifest['scripts']:
                        manifest['scripts'][category] = []
                    
                    # Calculate relative path from base_dir
                    try:
                        rel_path = script_path.relative_to(base_dir)
                    except ValueError:
                        rel_path = script_path.name
                    
                    # Generate script ID
                    script_id = self._generate_script_id(str(rel_path))
                    
                    # Calculate checksum
                    checksum = self._calculate_checksum(script_path)
                    
                    manifest['scripts'][category].append({
                        "id": script_id,
                        "name": metadata.get('name', script_path.stem),
                        "file_name": str(rel_path),
                        "description": metadata.get('description', ''),
                        "version": metadata.get('version', '1.0.0'),
                        "category": category,
                        "sha256": checksum
                    })
            else:
                # Flat list
                manifest['scripts'] = []
                for script_path, metadata in scripts:
                    try:
                        rel_path = script_path.relative_to(base_dir)
                    except ValueError:
                        rel_path = script_path.name
                    
                    script_id = self._generate_script_id(str(rel_path))
                    checksum = self._calculate_checksum(script_path)
                    
                    manifest['scripts'].append({
                        "id": script_id,
                        "name": metadata.get('name', script_path.stem),
                        "file_name": str(rel_path),
                        "description": metadata.get('description', ''),
                        "version": metadata.get('version', '1.0.0'),
                        "category": metadata.get('category', 'custom'),
                        "sha256": checksum
                    })
            
            # Write manifest file
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error creating manifest: {e}")
            return False
    
    def list_custom_manifests(self) -> List[Dict[str, any]]:
        """List all created custom manifests (stub for backward compatibility)"""
        # This method reads from config to list configured manifests
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
                manifests.append({
                    'name': name,
                    'url': url,
                    'verify_checksums': manifest_config.get('verify_checksums', True),
                    'type': 'remote' if url.startswith('http') else 'local'
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
