"""Repository management for LV Script Manager GUI"""

import json
import hashlib
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
import logging

class ChecksumVerificationError(Exception):
    """Raised when checksum verification fails"""
    pass

class ScriptRepository:
    """Manages remote script repository, caching, and updates"""
    
    def __init__(self):
        self.default_repo_url = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main"
        self.config_dir = Path.home() / ".lv_linux_learn"
        self.config_file = self.config_dir / "config.json"
        self.manifest_file = self.config_dir / "manifest.json"
        self.manifest_meta_file = self.config_dir / "manifest_metadata.json"
        self.script_cache_dir = self.config_dir / "script_cache"
        self.log_file = self.config_dir / "logs" / "repository.log"
        
        # Initialize
        self._ensure_directories()
        self._init_config()
        self.config = self.load_config()
        
        # Set repo_url based on configuration (custom or default)
        self.repo_url = self.get_effective_repository_url()
        
        # Set up logging
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.INFO,
            format='[%(asctime)s] %(message)s'
        )
    
    def get_effective_repository_url(self):
        """Get the effective repository URL (custom or default)"""
        # Check environment variable first
        custom_url = os.environ.get('CUSTOM_MANIFEST_URL', '').strip()
        if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
            # Extract base URL from manifest URL
            if custom_url.endswith('/manifest.json'):
                return custom_url[:-len('/manifest.json')]
            return custom_url
        
        # Check configuration file
        if hasattr(self, 'config'):
            custom_url = self.config.get('custom_manifest_url', '').strip()
            if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
                # Extract base URL from manifest URL
                if custom_url.endswith('/manifest.json'):
                    return custom_url[:-len('/manifest.json')]
                return custom_url
        
        # Default fallback
        return self.default_repo_url
    
    def get_manifest_url(self):
        """Get the manifest URL (custom or default)"""
        # Check environment variable first
        custom_url = os.environ.get('CUSTOM_MANIFEST_URL', '').strip()
        if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
            return custom_url
        
        # Check configuration file
        if hasattr(self, 'config'):
            custom_url = self.config.get('custom_manifest_url', '').strip()
            if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
                return custom_url
        
        # Default fallback
        return f"{self.default_repo_url}/manifest.json"
    
    def refresh_repository_url(self):
        """Refresh the repository URL from current configuration"""
        self.config = self.load_config()
        self.repo_url = self.get_effective_repository_url()
    
    def calculate_script_checksum(self, script_id):
        """Download a script and calculate its checksum (for manifest generation)"""
        script = self.get_script_by_id(script_id)
        if not script:
            return None
        
        download_url = script.get('download_url')
        if not download_url:
            return None
        
        try:
            with urllib.request.urlopen(download_url, timeout=30) as response:
                content = response.read()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logging.error(f"Failed to calculate checksum for {script_id}: {e}")
            return None
        
    def _ensure_directories(self):
        """Create necessary directories"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)
        self.script_cache_dir.mkdir(exist_ok=True)
        (self.script_cache_dir / "install").mkdir(exist_ok=True)
        (self.script_cache_dir / "tools").mkdir(exist_ok=True)
        (self.script_cache_dir / "exercises").mkdir(exist_ok=True)
        (self.script_cache_dir / "uninstall").mkdir(exist_ok=True)
    
    def _init_config(self):
        """Initialize config file with defaults"""
        if not self.config_file.exists():
            default_config = {
                "version": "1.0.0",
                "repository_url": self.default_repo_url,
                "use_remote_scripts": True,
                "fallback_to_bundled": False,
                "auto_check_updates": True,
                "auto_install_updates": True,
                "update_check_interval_minutes": 30,
                "last_update_check": None,
                "allow_insecure_downloads": False,
                "cache_timeout_days": 30,
                "verify_checksums": True
            }
            self.save_config(default_config)
        
        if not self.manifest_meta_file.exists():
            default_meta = {
                "last_fetch": None,
                "manifest_version": None,
                "cached_scripts": []
            }
            with open(self.manifest_meta_file, 'w') as f:
                json.dump(default_meta, f, indent=2)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {}
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False
    
    def get_config_value(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set_config_value(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
        return self.save_config(self.config)
    
    def fetch_remote_manifest(self):
        """Download the latest manifest from repository"""
        manifest_url = self.get_manifest_url()
        logging.info(f"Fetching manifest from {manifest_url}")
        
        try:
            with urllib.request.urlopen(manifest_url, timeout=30) as response:
                data = response.read().decode('utf-8')
                manifest = json.loads(data)
                
                # Save manifest
                with open(self.manifest_file, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                # Update metadata
                meta = {
                    "last_fetch": datetime.now().isoformat(),
                    "manifest_version": manifest.get('repository_version', 'unknown'),
                    "cached_scripts": []
                }
                with open(self.manifest_meta_file, 'w') as f:
                    json.dump(meta, f, indent=2)
                
                logging.info(f"Manifest fetched successfully (version: {meta['manifest_version']})")
                self.set_config_value("last_update_check", datetime.now().isoformat())
                
                return True
                
        except Exception as e:
            logging.error(f"Failed to fetch manifest: {e}")
            return False
    
    def load_local_manifest(self):
        """Load manifest from local cache"""
        if not self.manifest_file.exists():
            return None
        
        try:
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load local manifest: {e}")
            return None
    
    def parse_manifest(self):
        """Parse manifest and return script list"""
        manifest = self.load_local_manifest()
        if not manifest:
            return []
        
        return manifest.get('scripts', [])
    
    def get_script_by_id(self, script_id):
        """Get script information by ID"""
        scripts = self.parse_manifest()
        for script in scripts:
            if script.get('id') == script_id:
                return script
        return None
    
    def get_script_by_filename(self, filename):
        """Get script information by filename"""
        scripts = self.parse_manifest()
        for script in scripts:
            if script.get('file_name') == filename:
                return script
        return None
    
    def is_update_check_needed(self):
        """Check if it's time to check for updates"""
        last_check_str = self.get_config_value("last_update_check")
        interval_minutes = self.get_config_value("update_check_interval_minutes", 30)
        
        if not last_check_str:
            return True
        
        try:
            last_check = datetime.fromisoformat(last_check_str)
            now = datetime.now()
            diff = (now - last_check).total_seconds() / 60
            
            return diff >= interval_minutes
        except:
            return True
    
    def check_for_updates(self):
        """Check for available updates"""
        logging.info("Checking for updates...")
        
        # Fetch latest manifest
        if not self.fetch_remote_manifest():
            logging.info("Failed to fetch manifest, using cached version")
            return 0
        
        # Count updates
        update_count = 0
        scripts = self.parse_manifest()
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            remote_checksum = script.get('checksum', '').replace('sha256:', '')
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                local_checksum = self._calculate_checksum(str(cached_path))
                if local_checksum != remote_checksum:
                    update_count += 1
        
        logging.info(f"Found {update_count} updates available")
        
        # Auto-install if enabled
        if update_count > 0 and self.get_config_value("auto_install_updates", False):
            logging.info("Auto-installing updates...")
            self.update_all_scripts_silent()
            update_count = 0
        
        return update_count
    
    def list_available_updates(self):
        """Get list of scripts with available updates"""
        updates = []
        scripts = self.parse_manifest()
        
        for script in scripts:
            category = script.get('category')
            filename = script.get('file_name')
            remote_checksum = script.get('checksum', '').replace('sha256:', '')
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                local_checksum = self._calculate_checksum(str(cached_path))
                if local_checksum != remote_checksum:
                    updates.append(script)
        
        return updates
    
    def download_script(self, script_id):
        """Download a script from repository"""
        logging.info(f"Downloading script: {script_id}")
        
        script = self.get_script_by_id(script_id)
        if not script:
            logging.error(f"Script not found in manifest: {script_id}")
            return False
        
        download_url = script.get('download_url')
        filename = script.get('file_name')
        category = script.get('category')
        checksum = script.get('checksum', '').replace('sha256:', '')
        
        if not all([download_url, filename, category]):
            logging.error(f"Incomplete script information for {script_id}")
            return False
        
        dest_path = self.script_cache_dir / category / filename
        
        try:
            # Download script
            with urllib.request.urlopen(download_url, timeout=30) as response:
                content = response.read()
            
            # Verify checksum
            if self.get_config_value("verify_checksums", True) and checksum:
                actual_checksum = hashlib.sha256(content).hexdigest()
                if actual_checksum != checksum:
                    logging.error(f"Checksum verification failed for {script_id}: expected {checksum}, got {actual_checksum}")
                    logging.info(f"To fix this issue: Either update the manifest with correct checksum 'sha256:{actual_checksum}' or disable checksum verification")
                    raise ChecksumVerificationError(f"Checksum verification failed for {script_id}")
            elif not checksum:
                logging.warning(f"No checksum provided for {script_id}, skipping verification")
            
            # Save script
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(content)
            
            # Make executable
            dest_path.chmod(0o755)
            
            logging.info(f"Downloaded successfully: {dest_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to download {script_id}: {e}")
            return False
    
    def _calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return ""
    
    def verify_checksum(self, filepath, expected_checksum):
        """Verify file checksum"""
        expected_checksum = expected_checksum.replace('sha256:', '')
        actual_checksum = self._calculate_checksum(filepath)
        return actual_checksum == expected_checksum
    
    def install_remote_script(self, script_id):
        """Install a script from repository"""
        return self.download_script(script_id)
    
    def update_single_script(self, script_id):
        """Update a single script"""
        logging.info(f"Updating script: {script_id}")
        return self.download_script(script_id)
    
    def update_all_scripts(self):
        """Update all cached scripts"""
        scripts = self.parse_manifest()
        updated = 0
        failed = 0
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            
            cached_path = self.script_cache_dir / category / filename
            
            # Only update if already cached
            if cached_path.exists():
                if self.download_script(script_id):
                    updated += 1
                else:
                    failed += 1
        
        logging.info(f"Batch update: {updated} updated, {failed} failed")
        return updated, failed
    
    def update_all_scripts_silent(self):
        """Update all cached scripts without logging to console"""
        scripts = self.parse_manifest()
        updated = 0
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                if self.download_script(script_id):
                    updated += 1
        
        logging.info(f"Silent update complete: {updated} scripts updated")
        return updated
    
    def get_cached_script_path(self, script_id):
        """Get path to cached script"""
        script = self.get_script_by_id(script_id)
        if not script:
            return None
        
        category = script.get('category')
        filename = script.get('file_name')
        
        if not category or not filename:
            return None
        
        cached_path = self.script_cache_dir / category / filename
        
        if cached_path.exists():
            return str(cached_path)
        
        return None
    
    def is_script_cached(self, script_id):
        """Check if script is cached locally"""
        return self.get_cached_script_path(script_id) is not None
    
    def list_cached_scripts(self):
        """Get list of cached scripts"""
        cached = []
        
        for category_dir in self.script_cache_dir.iterdir():
            if category_dir.is_dir():
                for script_file in category_dir.glob("*.sh"):
                    script = self.get_script_by_filename(script_file.name)
                    if script:
                        cached.append(script)
        
        return cached
    
    def clear_cache(self):
        """Clear all cached scripts"""
        import shutil
        
        for category_dir in self.script_cache_dir.iterdir():
            if category_dir.is_dir():
                for script_file in category_dir.glob("*.sh"):
                    script_file.unlink()
        
        logging.info("Cache cleared by user")
        return True
        
    def get_repository_url(self):
        """Get the repository URL from the current manifest"""
        try:
            manifest = self.load_local_manifest()
            if manifest and 'repository_url' in manifest:
                return manifest['repository_url']
            return self.repo_url  # fallback to default
        except Exception:
            return self.repo_url

    def ensure_includes_available(self):
        """Ensure includes are available for the current repository"""
        manifest = self.load_local_manifest()
        if not manifest:
            return False
            
        repo_url = manifest.get('repository_url', self.repo_url)
        return self._download_repository_includes(repo_url)
    
    def _download_repository_includes(self, repo_url):
        """Download includes directory from the specified repository URL"""
        try:
            includes_cache_dir = self.script_cache_dir / "includes"
            
            # Check if includes are already fresh for this repository
            if self._are_includes_fresh(repo_url, includes_cache_dir):
                return True
                
            # Create includes cache directory
            includes_cache_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Downloading includes from {repo_url}")
            
            # Get includes files list from manifest (if available)
            includes_files = self._get_includes_files_list()
            
            # Always try to download main.sh (required)
            success = False
            main_url = f"{repo_url}/includes/main.sh"
            main_file = includes_cache_dir / "main.sh"
            
            try:
                with urllib.request.urlopen(main_url, timeout=30) as response:
                    content = response.read()
                    
                with open(main_file, 'wb') as f:
                    f.write(content)
                main_file.chmod(0o644)
                success = True
                logging.info("Downloaded main.sh successfully")
            except Exception as e:
                logging.error(f"Failed to download main.sh: {e}")
                return False
            
            # Download additional includes files
            for filename in includes_files:
                if filename == "main.sh":
                    continue  # Already downloaded
                    
                try:
                    file_url = f"{repo_url}/includes/{filename}"
                    file_path = includes_cache_dir / filename
                    
                    with urllib.request.urlopen(file_url, timeout=30) as response:
                        content = response.read()
                        
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    file_path.chmod(0o644)
                    logging.info(f"Downloaded {filename} successfully")
                except Exception as e:
                    logging.warning(f"Optional file {filename} not available: {e}")
            
            # Mark the includes as fresh for this repository
            self._mark_includes_fresh(repo_url, includes_cache_dir)
            
            logging.info(f"Successfully downloaded includes from {repo_url}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to download includes from {repo_url}: {e}")
            return False
            
    def _get_includes_files_list(self):
        """Get list of includes files to download (from manifest or defaults)"""
        try:
            manifest = self.load_local_manifest()
            if manifest and 'includes_files' in manifest:
                return manifest['includes_files']
        except Exception:
            pass
            
        # Default includes files to try
        return ["main.sh", "repository.sh"]
    
    def _are_includes_fresh(self, repo_url, includes_dir):
        """Check if cached includes are fresh for the specified repository"""
        if not includes_dir.exists():
            return False
            
        origin_file = includes_dir / ".origin"
        timestamp_file = includes_dir / ".timestamp"
        
        if not (origin_file.exists() and timestamp_file.exists()):
            return False
            
        try:
            # Check if origin matches current repository
            with open(origin_file, 'r') as f:
                cached_origin = f.read().strip()
            if cached_origin != repo_url:
                return False
                
            # Check if timestamp is less than 24 hours old
            with open(timestamp_file, 'r') as f:
                cache_time = int(f.read().strip())
            current_time = int(time.time())
            
            # 24 hour cache
            return (current_time - cache_time) < 86400
            
        except Exception:
            return False
    
    def _mark_includes_fresh(self, repo_url, includes_dir):
        """Mark includes as fresh for the specified repository"""
        try:
            origin_file = includes_dir / ".origin"
            timestamp_file = includes_dir / ".timestamp"
            
            with open(origin_file, 'w') as f:
                f.write(repo_url)
                
            with open(timestamp_file, 'w') as f:
                f.write(str(int(time.time())))
                
        except Exception as e:
            logging.error(f"Failed to mark includes as fresh: {e}")
    
    def count_cached_scripts(self):
        """Count number of cached scripts"""
        count = 0
        for category_dir in self.script_cache_dir.iterdir():
            if category_dir.is_dir():
                count += len(list(category_dir.glob("*.sh")))
        return count
    
    def resolve_script_path(self, filename):
        """Resolve script path (cached version)"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            return None
        
        script_id = script.get('id')
        cached_path = self.get_cached_script_path(script_id)
        
        if cached_path:
            return cached_path
        
        # No bundled fallback per requirements
        return None
    
    def get_script_status(self, filename):
        """Get status of a script (cached, outdated, not_installed)"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            return "unknown"
        
        category = script.get('category')
        remote_checksum = script.get('checksum', '').replace('sha256:', '')
        
        cached_path = self.script_cache_dir / category / filename
        
        if cached_path.exists():
            local_checksum = self._calculate_checksum(str(cached_path))
            
            if local_checksum == remote_checksum:
                return "cached"
            else:
                return "outdated"
        else:
            return "not_installed"
    
    def get_script_version(self, filename):
        """Get version of a script"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            return "unknown"
        
        return script.get('version', 'unknown')
    
    def download_all_scripts(self):
        """Download all scripts from repository (initial setup)"""
        if not self.manifest_file.exists():
            if not self.fetch_remote_manifest():
                return 0, 0
        
        scripts = self.parse_manifest()
        downloaded = 0
        failed = 0
        
        for script in scripts:
            script_id = script.get('id')
            
            if self.download_script(script_id):
                downloaded += 1
            else:
                failed += 1
        
        logging.info(f"Initial download: {downloaded} scripts downloaded")
        return downloaded, failed
