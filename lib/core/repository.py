"""Repository management for LV Script Manager GUI

Consolidated module combining:
- ScriptRepository: Core cache and manifest management
- Repository operations: High-level download/update/remove operations with feedback
"""

import json
import hashlib
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple, List, Any, Union

# Debug logging flag (disabled by default). Set LV_DEBUG_CACHE=1 to enable.
DEBUG_CACHE: bool = os.environ.get("LV_DEBUG_CACHE") == "1"

class ChecksumVerificationError(Exception):
    """Raised when checksum verification fails"""
    pass

class ScriptRepository:
    """Manages remote script repository, caching, and updates"""
    
    def __init__(self) -> None:
        self.default_repo_url = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main"
        self.config_dir: Path = Path.home() / ".lv_linux_learn"
        self.config_file: Path = self.config_dir / "config.json"
        self.manifest_file: Path = self.config_dir / "manifest.json"
        self.manifest_meta_file: Path = self.config_dir / "manifest_metadata.json"
        self.script_cache_dir: Path = self.config_dir / "script_cache"
        self.log_file: Path = self.config_dir / "logs" / "repository.log"
        
        # Initialize directories and config first
        self._ensure_directories()
        self._init_config()
        self.config = self.load_config()
        
        # Detect if running from local repository (requires config to be loaded)
        self.local_repo_root: Path | None = self._detect_local_repository()
        
        # Set repo_url based on configuration (custom or default)
        self.repo_url: str = self.get_effective_repository_url()
        
        # Set up logging
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.INFO,
            format='[%(asctime)s] %(message)s'
        )
    
    def get_effective_repository_url(self) -> str:
        """Get the effective repository URL (custom or default).
        
        Prioritizes custom URL from environment or config file over default.
        Extracts base URL from manifest URLs when needed.
        
        Returns:
            str: The effective repository base URL
        """
        # Check environment variable first
        custom_url: str = os.environ.get('CUSTOM_MANIFEST_URL', '').strip()
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
    
    def get_manifest_url(self) -> str:
        """Get the manifest URL (custom or default).
        
        Returns the full URL to the manifest.json file. Prioritizes custom
        manifest URL from environment or config file over default.
        
        Returns:
            str: The full manifest URL
        """
        # Check environment variable first
        custom_url: str = os.environ.get('CUSTOM_MANIFEST_URL', '').strip()
        if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
            return custom_url
        
        # Check configuration file
        if hasattr(self, 'config'):
            custom_url = self.config.get('custom_manifest_url', '').strip()
            if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
                return custom_url
        
        # Default fallback
        return f"{self.default_repo_url}/manifest.json"
    
    def refresh_repository_url(self) -> None:
        """Refresh the repository URL from current configuration.
        
        Reloads config from file and updates internal URL references.
        Useful after configuration changes via CLI or API.
        """
        self.config = self.load_config()
        self.repo_url: str = self.get_effective_repository_url()
    
    def _detect_local_repository(self) -> Optional[Path]:
        """Detect if running from a local git repository of lv_linux_learn.
        
        Checks if force_remote_downloads is enabled. If true, returns None.
        Otherwise searches parent directories for local repository markers.
        
        Returns:
            Optional[Path]: Path to local repository root if found and enabled, None otherwise
        """
        # Check config file setting first - default is True (force remote downloads)
        if self.get_config_value("force_remote_downloads", True):
            logging.info("Local repository detection disabled (force_remote_downloads=true in config)")
            return None
        
        # Allow disabling local repo detection via environment variable (for quick override)
        if os.environ.get('LV_FORCE_REMOTE', '').lower() in ('1', 'true', 'yes'):
            logging.info("Local repository detection disabled (LV_FORCE_REMOTE environment variable set)")
            return None
        
        # Check common locations for local repository
        possible_paths: List[Path] = [
            Path.home() / "lv_linux_learn",
            Path.cwd(),
            Path(__file__).parent.parent,  # lib/../ = repo root
        ]
        
        for path in possible_paths:
            if path.exists():
                # Check for manifest.json and scripts/ directory as indicators
                if (path / "manifest.json").exists() and (path / "scripts").exists():
                    logging.info(f"Local repository detected at: {path}")
                    return path
        
        return None
    
    def _get_local_script_path(self, script_id, manifest_path=None):
        """Get path to script in local repository if available
        
        Args:
            script_id: Script ID to find
            manifest_path: Optional specific manifest
            
        Returns:
            Path object if found, None otherwise
        """
        if not self.local_repo_root:
            return None
        
        # Get script info from manifest
        script = self.get_script_by_id(script_id, manifest_path=manifest_path)
        if not script:
            return None
        
        # Build local path
        file_name = script.get('file_name') or script.get('name')  # Fallback to 'name' field
        category = script.get('category')
        
        if not file_name:
            return None
        
        if category == 'install':
            local_path = self.local_repo_root / "scripts" / file_name
        elif category == 'tools':
            local_path = self.local_repo_root / "tools" / file_name
        elif category == 'exercises':
            local_path = self.local_repo_root / "bash_exercises" / file_name
        elif category == 'uninstall':
            local_path = self.local_repo_root / "uninstallers" / file_name
        elif category == 'includes':
            local_path = self.local_repo_root / "includes" / file_name
        else:
            return None
        
        if local_path.exists():
            return local_path
        
        return None
    
    def calculate_script_checksum(self, script_id: str) -> Optional[str]:
        """Download a script and calculate its checksum (for manifest generation).
        
        Downloads script from repository and computes SHA256 hash.
        Used during manifest creation/updates.
        
        Args:
            script_id: Script ID to download
            
        Returns:
            Optional[str]: SHA256 checksum hex string, or None on error
        """
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
        
    def _ensure_directories(self) -> None:
        """Create necessary cache and config directories.
        
        Initializes the following directory structure:
        - ~/.lv_linux_learn/         (config directory)
        - ~/.lv_linux_learn/logs/    (log files)
        - ~/.lv_linux_learn/script_cache/   (cached scripts)
        - Subdirectories for each category (install, tools, exercises, uninstall)
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)
        self.script_cache_dir.mkdir(exist_ok=True)
        (self.script_cache_dir / "install").mkdir(exist_ok=True)
        (self.script_cache_dir / "tools").mkdir(exist_ok=True)
        (self.script_cache_dir / "exercises").mkdir(exist_ok=True)
        (self.script_cache_dir / "uninstall").mkdir(exist_ok=True)
    
    def _init_config(self) -> None:
        """Initialize config file with defaults if not present.
        
        Creates default configuration with sensible defaults:
        - force_remote_downloads: True (GitHub-first behavior)
        - verify_checksums: True (security)
        - auto_check_updates: True (keep user informed)
        - manifest_cache_max_age_seconds: 60 (cache duration)
        
        Also creates manifest metadata file for tracking fetches and cache status.
        """
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
                "verify_checksums": True,
                "force_remote_downloads": True,
                "manifest_cache_max_age_seconds": 60
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
    
    def load_config(self) -> dict:
        """Load configuration from file.
        
        Reads ~/.lv_linux_learn/config.json and ensures required keys exist
        with appropriate defaults (e.g., manifest_cache_max_age_seconds).
        
        Returns:
            dict: Configuration dictionary with all expected keys
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                if "manifest_cache_max_age_seconds" not in config:
                    config["manifest_cache_max_age_seconds"] = 60
                return config
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {}
    
    def save_config(self, config: dict) -> bool:
        """Save configuration to file.
        
        Writes configuration dict to ~/.lv_linux_learn/config.json
        and updates internal config reference.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            bool: True if saved successfully, False on error
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False
    
    def get_config_value(self, key: str, default=None):
        """Get a configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
            
        Returns:
            Any: Configuration value, or default if not present
        """
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value) -> bool:
        """Set a configuration value and persist to file.
        
        Updates internal config dict and saves to disk immediately.
        
        Args:
            key: Configuration key to set
            value: Value to set (any JSON-serializable type)
            
        Returns:
            bool: True if saved successfully, False on error
        """
        self.config[key] = value
        return self.save_config(self.config)
    
    def fetch_remote_manifest(self) -> bool:
        """Download the latest manifest from repository.
        
        Fetches manifest.json from configured repository URL with 30s timeout.
        Saves to local manifest file and updates metadata.
        
        Returns:
            Optional[dict]: Parsed manifest dict, or None on download/parse error
        """
        manifest_url: str = self.get_manifest_url()
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
    
    def load_local_manifest(self) -> Optional[Any]:
        """Load manifest from local cache or custom manifest"""
        # Check if we should use a custom manifest
        custom_manifest_url = self.config.get('custom_manifest_url', '').strip()
        use_public_repo = self.config.get('use_public_repository', True)
        
        # If public repo is disabled and we have a custom manifest, load that
        if not use_public_repo and custom_manifest_url:
            if custom_manifest_url.startswith('file://'):
                # Load from local file
                custom_path = Path(custom_manifest_url[7:])  # Remove 'file://'
                if custom_path.exists():
                    try:
                        with open(custom_path, 'r') as f:
                            return json.load(f)
                    except Exception as e:
                        logging.error(f"Failed to load custom manifest from {custom_path}: {e}")
            elif custom_manifest_url.startswith(('http://', 'https://')):
                # For online custom manifests, we should have cached it
                # Fall through to load from cache
                pass
        
        # Load from cached manifest (public or online custom)
        if not self.manifest_file.exists():
            return None
        
        try:
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load local manifest: {e}")
            return None
    
    def parse_manifest(self) -> List[dict]:
        """Parse manifest and return script list.
        
        Handles both flat array format and nested dictionary format.
        Flat: [{"id": "chrome", ...}, ...]
        Nested: {"install": [{...}], "tools": [{...}], ...}
        
        Returns:
            List[dict]: List of script metadata dictionaries, empty list if no manifest
        """
        manifest: Optional[Any] = self.load_local_manifest()
        if not manifest:
            return []
        
        scripts_data = manifest.get('scripts', [])
        
        # Handle both formats: flat array and nested dictionary
        if isinstance(scripts_data, dict):
            # Custom manifest format: nested by category
            all_scripts = []
            for category, category_scripts in scripts_data.items():
                for script in category_scripts:
                    script['category'] = category  # Ensure category is set
                    all_scripts.append(script)
            return all_scripts
        else:
            # Default format: flat array
            return scripts_data
    
    def get_script_by_id(self, script_id: str, manifest_path: Optional[Path] = None) -> Optional[dict]:
        """Get script information by ID.
        
        Searches loaded manifest or specific custom manifest for script metadata.
        Handles both flat array and nested dictionary manifest formats.
        
        Args:
            script_id: Script ID to find (e.g., 'chrome', 'docker', 'zeroiter_tools')
            manifest_path: Optional path to specific manifest file (for custom manifests)
            
        Returns:
            Optional[dict]: Script metadata dict if found, None otherwise
        """
        if manifest_path:
            # Load from specific custom manifest
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    scripts_data = manifest.get('scripts', [])
                    # Handle both formats
                    if isinstance(scripts_data, dict):
                        all_scripts = []
                        for category, category_scripts in scripts_data.items():
                            for script in category_scripts:
                                script['category'] = category
                                all_scripts.append(script)
                        scripts_data = all_scripts
                    
                    for script in scripts_data:
                        if script.get('id') == script_id:
                            return script
            except Exception as e:
                logging.error(f"Failed to load manifest from {manifest_path}: {e}")
                return None
        else:
            # First search custom manifests from config
            try:
                config = json.loads(self.config_file.read_text())
                custom_manifests = config.get('custom_manifests', {})
                
                for manifest_name, manifest_info in custom_manifests.items():
                    manifest_data = manifest_info.get('manifest_data')
                    if manifest_data:
                        scripts_data = manifest_data.get('scripts', [])
                        # Handle both formats
                        if isinstance(scripts_data, dict):
                            all_scripts = []
                            for category, category_scripts in scripts_data.items():
                                for script in category_scripts:
                                    script['category'] = category
                                    all_scripts.append(script)
                            scripts_data = all_scripts
                        
                        for script in scripts_data:
                            if script.get('id') == script_id:
                                return script
            except Exception as e:
                logging.debug(f"No custom manifests in config or error reading: {e}")
            
            # Then search default/cached public manifest
            scripts = self.parse_manifest()
            for script in scripts:
                if script.get('id') == script_id:
                    return script
        return None
    
    def get_script_by_filename(self, filename: str) -> Optional[dict]:
        """Get script information by filename.
        
        Searches manifest for script with matching file_name field.
        
        Args:
            filename: Script filename to search for
            
        Returns:
            Optional[dict]: Script metadata if found, None otherwise
        """
        scripts = self.parse_manifest()
        for script in scripts:
            if script.get('file_name') == filename:
                return script
        return None
    
    def is_update_check_needed(self) -> bool:
        """Check if it's time to check for updates.
        
        Compares time since last update check with configured interval.
        Returns True if interval has elapsed or no previous check recorded.
        
        Returns:
            bool: True if update check should be performed, False if interval not elapsed
        """
        if not self.config_file.exists():
            return True

        last_check_str = self.get_config_value("last_update_check")
        interval_minutes = self.get_config_value("update_check_interval_minutes", 30) or 30
        
        if not last_check_str:
            return True
        
        try:
            last_check: datetime = datetime.fromisoformat(last_check_str)
            now: datetime = datetime.now()
            diff: float = (now - last_check).total_seconds() / 60
            
            return diff >= interval_minutes
        except:
            return True
    
    def check_for_updates(self) -> int:
        """Check for available updates.
        
        Fetches latest manifest from repository and compares with cached scripts.
        Returns count of scripts with available updates.
        
        Returns:
            int: Number of updates available for cached scripts
        """
        logging.info("Checking for updates...")
        
        # Fetch latest manifest
        if not self.fetch_remote_manifest():
            logging.info("Failed to fetch manifest, using cached version")
            return 0
        
        # Update timestamp immediately after successful manifest fetch (Issue #2 FIX)
        self.set_config_value("last_update_check", datetime.now().isoformat())
        
        # Count updates
        update_count = 0
        scripts = self.parse_manifest()
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            remote_checksum_raw = script.get('checksum', '')
            
            # Skip scripts without required fields
            if not all([category, filename]):
                continue
            
            # Handle empty checksum (Issue #1 FIX - validate checksum exists)
            if not remote_checksum_raw:
                logging.debug(f"No checksum for {script_id}, skipping update check")
                continue
            
            # Normalize checksum - remove 'sha256:' prefix if present
            remote_checksum = remote_checksum_raw.replace('sha256:', '')
            
            if not all([category, filename]):
                continue
            
            # Type narrowing: assert category and filename are not None
            assert category is not None and filename is not None
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                try:
                    local_checksum: str = self._calculate_checksum(str(cached_path))
                    # Issue #1 FIX: Properly compare checksums
                    if local_checksum and remote_checksum and local_checksum != remote_checksum:
                        logging.debug(f"Update available for {script_id}: {local_checksum[:16]}... != {remote_checksum[:16]}...")
                        update_count += 1
                    elif not local_checksum:
                        logging.warning(f"Failed to calculate checksum for {cached_path}")
                except Exception as e:
                    logging.warning(f"Error checking updates for {script_id}: {e}")
        
        logging.info(f"Found {update_count} updates available")
        
        # Issue #3 FIX: Auto-install if enabled - return count correctly
        if update_count > 0 and self.get_config_value("auto_install_updates", False):
            logging.info(f"Auto-installing {update_count} updates...")
            installed_count: int = self.update_all_scripts_silent()
            logging.info(f"Auto-installed {installed_count} updates")
            return 0  # Return 0 to indicate auto-install completed successfully
        
        return update_count
    
    def list_available_updates(self) -> List[dict]:
        """Get list of scripts with available updates.
        
        Compares cached scripts with remote manifest to identify updates.
        Returns only cached scripts that have newer versions available.
        
        Returns:
            List[dict]: List of script metadata dicts with available updates
        """
        updates = []
        scripts = self.parse_manifest()
        
        for script in scripts:
            category = script.get('category')
            filename = script.get('file_name')
            remote_checksum = script.get('checksum', '').replace('sha256:', '')
            
            if not all([category, filename]):
                continue
            
            # Type narrowing: assert category and filename are not None
            assert category is not None and filename is not None
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                local_checksum: str = self._calculate_checksum(str(cached_path))
                if local_checksum != remote_checksum:
                    updates.append(script)
        
        return updates
    
    def download_script(self, script_id, manifest_path=None):
        """Download a script from repository
        
        Args:
            script_id: Script ID to download
            manifest_path: Optional path to specific manifest file (for custom manifests)
        
        Returns:
            tuple: (success: bool, download_url: str)
        """
        logging.info(f"Downloading script: {script_id}" + (f" from {manifest_path}" if manifest_path else ""))
        
        script = self.get_script_by_id(script_id, manifest_path=manifest_path)
        if not script:
            logging.error(f"Script not found in manifest: {script_id}")
            return False, None
        
        # Ensure includes are available for this repository (critical for custom repos)
        if manifest_path:
            # Custom repository - download its includes
            try:
                with open(manifest_path, 'r') as f:
                    custom_manifest = json.load(f)
                    custom_repo_url = custom_manifest.get('repository_url')
                    if custom_repo_url:
                        logging.info(f"Ensuring includes available for custom repository: {custom_repo_url}")
                        self._download_repository_includes(custom_repo_url)
            except Exception as e:
                logging.warning(f"Failed to ensure includes for custom repository: {e}")
        else:
            # Default repository - use standard includes method
            self.ensure_includes_available()
        
        download_url = script.get('download_url') or script.get('path')  # Fallback to 'path' field for compatibility
        filename = script.get('file_name') or script.get('name')  # Fallback to 'name' field
        category = script.get('category')
        checksum = script.get('checksum', '').replace('sha256:', '')
        
        if not all([download_url, filename, category]):
            logging.error(f"Incomplete script information for {script_id}")
            return False, None
        
        # Type narrowing: at this point we know category and filename are not None
        assert category is not None and filename is not None
        
        dest_path = self.script_cache_dir / category / filename
        
        # Try to use local repository file first (skip GitHub CDN cache issues)
        local_script_path = self._get_local_script_path(script_id, manifest_path=manifest_path)
        if local_script_path and local_script_path.exists():
            try:
                logging.info(f"Using local repository file: {local_script_path}")
                with open(local_script_path, 'rb') as f:
                    content: bytes = f.read()
                
                # Save to cache
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'wb') as f:
                    f.write(content)
                
                # Make executable
                os.chmod(str(dest_path), 0o755)
                logging.info(f"Successfully copied local script to cache: {script_id}")
                return True, str(local_script_path), None
                
            except Exception as e:
                logging.warning(f"Failed to copy local file, falling back to download: {e}")
                # Fall through to download
        
        try:
            # Type narrowing: at this point we know download_url is not None
            assert download_url is not None
            
            # Handle file:// URLs separately
            if download_url.startswith('file://'):
                local_file = download_url.replace('file://', '')
                logging.info(f"Copying from local file: {local_file}")
                
                if not os.path.exists(local_file):
                    logging.error(f"Local file not found: {local_file}")
                    return False, None, "Local file not found"
                
                with open(local_file, 'rb') as f:
                    content: bytes = f.read()
            else:
                # Download script from remote URL
                logging.info(f"Downloading from remote: {download_url}")
                with urllib.request.urlopen(download_url, timeout=30) as response:
                    content = response.read()
            
            # Check if checksum verification is enabled
            # First check the manifest-level setting, then fall back to global config
            if manifest_path:
                # Load from specific custom manifest
                try:
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                except Exception as e:
                    logging.warning(f"Failed to load manifest from {manifest_path}: {e}")
                    manifest = None
            else:
                # Load default/public manifest
                manifest: Optional[Any] = self.load_local_manifest()
            
            manifest_verify_checksums: Optional[Any] = manifest.get('verify_checksums') if manifest else None
            
            # Use manifest setting if explicitly set, otherwise use global config
            if manifest_verify_checksums is not None:
                should_verify = manifest_verify_checksums
            else:
                should_verify = self.get_config_value("verify_checksums", True)
            
            # Verify checksum if enabled
            if should_verify and checksum:
                actual_checksum: str = hashlib.sha256(content).hexdigest()
                if actual_checksum != checksum:
                    # Type narrowing: download_url is guaranteed not None here
                    assert download_url is not None
                    # Retry once with cache-busting query param to avoid CDN stale content
                    cache_bust_url: str | None = f"{download_url}?t={int(time.time())}" if download_url.startswith("http") else None
                    if cache_bust_url:
                        logging.warning(
                            f"Checksum mismatch for {script_id}; retrying with cache-busted URL."
                        )
                        with urllib.request.urlopen(cache_bust_url, timeout=30) as response:
                            content = response.read()
                        actual_checksum: str = hashlib.sha256(content).hexdigest()

                    # Check again after retry (or if retry was skipped)
                    if actual_checksum != checksum:
                        logging.error(
                            f"Checksum verification failed for {script_id}: expected {checksum}, got {actual_checksum}"
                        )
                        logging.info(
                            f"To fix this issue: Either update the manifest with correct checksum 'sha256:{actual_checksum}' or disable checksum verification"
                        )
                        raise ChecksumVerificationError(f"Checksum verification failed for {script_id}")
            elif not checksum:
                if should_verify:
                    logging.warning(f"No checksum provided for {script_id}, skipping verification")
            else:
                logging.info(f"Checksum verification disabled for {script_id}")
            
            # Save script
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(content)
            
            # Make executable
            dest_path.chmod(0o755)
            
            logging.info(f"Downloaded successfully: {dest_path}")
            return True, download_url, None
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Failed to download {script_id}: {error_msg}")
            return False, download_url, error_msg
    
    def _calculate_checksum(self, filepath) -> str:
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
        actual_checksum: str = self._calculate_checksum(filepath)
        return actual_checksum == expected_checksum
    
    def install_remote_script(self, script_id):
        """Install a script from repository"""
        return self.download_script(script_id)
    
    def update_single_script(self, script_id):
        """Update a single script"""
        logging.info(f"Updating script: {script_id}")
        return self.download_script(script_id)
    
    def update_all_scripts(self) -> Tuple[int, int]:
        """Update all cached scripts"""
        scripts = self.parse_manifest()
        updated = 0
        failed = 0
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            
            if not all([category, filename]):
                continue
            
            # Type narrowing: assert category and filename are not None
            assert category is not None and filename is not None
            
            cached_path = self.script_cache_dir / category / filename
            
            # Only update if already cached
            if cached_path.exists():
                if self.download_script(script_id):
                    updated += 1
                else:
                    failed += 1
        
        logging.info(f"Batch update: {updated} updated, {failed} failed")
        return updated, failed
    
    def update_all_scripts_silent(self) -> int:
        """Update all cached scripts without logging to console"""
        scripts = self.parse_manifest()
        updated = 0
        
        for script in scripts:
            script_id = script.get('id')
            category = script.get('category')
            filename = script.get('file_name')
            
            if not all([category, filename]):
                continue
            
            # Type narrowing: assert category and filename are not None
            assert category is not None and filename is not None
            
            cached_path = self.script_cache_dir / category / filename
            
            if cached_path.exists():
                if self.download_script(script_id):
                    updated += 1
        
        logging.info(f"Silent update complete: {updated} scripts updated")
        return updated
    
    def get_cached_script_path(self, script_id=None, category=None, filename=None, manifest_path=None) -> str | None:
        """Get path to cached script
        
        Args:
            script_id: Script ID to look up (will search manifest)
            category: Direct category (bypasses manifest lookup if provided with filename)
            filename: Direct filename (bypasses manifest lookup if provided with category)
            manifest_path: Path to specific manifest file for script_id lookup
        """
        # If category and filename provided directly, skip manifest lookup
        if category and filename:
            cached_path = self.script_cache_dir / category / filename
            try:
                exists = cached_path.exists()
                pass  # removed debug log
            except Exception as e:
                pass  # removed debug log
            if cached_path.exists():
                return str(cached_path)
            return None
        
        # Otherwise, look up script by ID
        if not script_id:
            pass  # removed debug log
            return None
            
        script = self.get_script_by_id(script_id, manifest_path=manifest_path)
        if not script:
            pass  # removed debug log
            return None
        
        category = script.get('category')
        filename = script.get('file_name') or script.get('name')  # Fallback to 'name' field
        
        if not category or not filename:
            pass  # removed debug log
            return None
        
        cached_path = self.script_cache_dir / category / filename
        
        exists = cached_path.exists()
        pass  # removed debug log
        if exists:
            return str(cached_path)

        # Fallback: search for cached file by filename across categories
        try:
            for category_dir in self.script_cache_dir.iterdir():
                if category_dir.is_dir():
                    candidate = category_dir / filename
                    if candidate.exists():
                        return str(candidate)
        except Exception:
            pass
        
        return None
    
    def is_script_cached(self, script_id) -> bool:
        """Check if script is cached locally"""
        path: str | None = self.get_cached_script_path(script_id)
        result: bool = path is not None
        pass  # removed debug log
        return result
    
    def list_cached_scripts(self):
        """Get list of cached scripts"""
        cached = []
        
        for category_dir in self.script_cache_dir.iterdir():
            if category_dir.is_dir():
                for script_file in category_dir.glob("*.sh"):
                    script = self.get_script_by_filename(script_file.name)
                    if script:
                        cached.append(script)
        
        pass  # removed debug log
        return cached
    
    def clear_cache(self) -> bool:
        """Clear all cached scripts"""
        import shutil
        
        removed = 0
        try:
            for category_dir in self.script_cache_dir.iterdir():
                if category_dir.is_dir():
                    # Remove all files in category directory (not just .sh files)
                    for script_file in category_dir.iterdir():
                        if script_file.is_file():
                            script_file.unlink()
                            removed += 1
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")
        
        logging.info(f"Cache cleared by user ({removed} files removed)")
        pass  # removed debug log
        return True
        
    def get_repository_url(self) -> Union[Any, str]:
        """Get the repository URL from the current manifest"""
        try:
            manifest: Optional[Any] = self.load_local_manifest()
            if manifest and 'repository_url' in manifest:
                return manifest['repository_url']
            return self.repo_url  # fallback to default
        except Exception:
            return self.repo_url

    def ensure_includes_available(self) -> bool:
        """Ensure includes are available for the current repository"""
        manifest: Optional[Any] = self.load_local_manifest()
        if not manifest:
            pass  # removed debug log
            return False
            
        repo_url = manifest.get('repository_url', self.repo_url)
        pass  # removed debug log
        return self._download_repository_includes(repo_url)
    
    def _download_repository_includes(self, repo_url) -> bool:
        """Download includes directory from the specified repository URL"""
        try:
            includes_cache_dir: Path = self.script_cache_dir / "includes"
            
            # Check if includes are already fresh for this repository
            if self._are_includes_fresh(repo_url, includes_cache_dir):
                pass  # removed debug log
                return True
                
            # Create includes cache directory
            includes_cache_dir.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"Downloading includes from {repo_url}")
            pass  # removed debug log
            
            # Get includes files list from manifest (if available)
            includes_files: Union[Any, List[str]] = self._get_includes_files_list()
            
            # Always try to download main.sh (required)
            success = False
            main_url: str = f"{repo_url}/includes/main.sh"
            main_file: Path = includes_cache_dir / "main.sh"
            
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
                pass  # removed debug log
                return False
            
            # Download additional includes files
            for filename in includes_files:
                if filename == "main.sh":
                    continue  # Already downloaded
                    
                try:
                    file_url: str = f"{repo_url}/includes/{filename}"
                    file_path: Union[Any, Path] = includes_cache_dir / filename
                    
                    with urllib.request.urlopen(file_url, timeout=30) as response:
                        content = response.read()
                        
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    file_path.chmod(0o644)
                    logging.info(f"Downloaded {filename} successfully")
                    pass  # removed debug log
                except Exception as e:
                    logging.warning(f"Optional file {filename} not available: {e}")
                    pass  # removed debug log
            
            # Mark the includes as fresh for this repository
            self._mark_includes_fresh(repo_url, includes_cache_dir)
            
            logging.info(f"Successfully downloaded includes from {repo_url}")
            pass  # removed debug log
            return True
            
        except Exception as e:
            logging.error(f"Failed to download includes from {repo_url}: {e}")
            pass  # removed debug log
            return False
            
    def _get_includes_files_list(self) -> Union[Any, List[str]]:
        """Get list of includes files to download (from manifest or defaults)"""
        try:
            manifest: Optional[Any] = self.load_local_manifest()
            if manifest and 'includes_files' in manifest:
                return manifest['includes_files']
        except Exception:
            pass
            
        # Default includes files to try
        return ["main.sh", "repository.sh"]
    
    def _are_includes_fresh(self, repo_url, includes_dir) -> bool:
        """Check if cached includes are fresh for the specified repository"""
        if not includes_dir.exists():
            pass  # removed debug log
            return False
            
        origin_file = includes_dir / ".origin"
        timestamp_file = includes_dir / ".timestamp"
        main_file = includes_dir / "main.sh"
        
        # CRITICAL: Check that actual include files exist, not just metadata
        origin_exists = origin_file.exists()
        timestamp_exists = timestamp_file.exists()
        main_exists = main_file.exists()
        if not (origin_exists and timestamp_exists and main_exists):
            pass  # removed debug log
            return False
            
        try:
            # Check if origin matches current repository
            with open(origin_file, 'r') as f:
                cached_origin: str = f.read().strip()
            if cached_origin != repo_url:
                pass  # removed debug log
                return False
                
            # Check if timestamp is less than 24 hours old
            with open(timestamp_file, 'r') as f:
                cache_time = int(f.read().strip())
            current_time = int(time.time())
            
            # 24 hour cache
            fresh: bool = (current_time - cache_time) < 86400
            pass  # removed debug log
            return fresh
            
        except Exception as e:
            pass  # removed debug log
            return False
    
    def _mark_includes_fresh(self, repo_url, includes_dir) -> None:
        """Mark includes as fresh for the specified repository"""
        try:
            origin_file = includes_dir / ".origin"
            timestamp_file = includes_dir / ".timestamp"
            
            with open(origin_file, 'w') as f:
                f.write(repo_url)
                
            with open(timestamp_file, 'w') as f:
                f.write(str(int(time.time())))
            pass  # removed debug log
                
        except Exception as e:
            logging.error(f"Failed to mark includes as fresh: {e}")
            pass  # removed debug log
    
    def count_cached_scripts(self) -> int:
        """Count number of cached scripts"""
        count = 0
        for category_dir in self.script_cache_dir.iterdir():
            if category_dir.is_dir():
                count += len(list(category_dir.glob("*.sh")))
        pass  # removed debug log
        return count
    
    def resolve_script_path(self, filename) -> None | str:
        """Resolve script path (cached version)"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            pass  # removed debug log
            return None
        
        script_id = script.get('id')
        cached_path: str | None = self.get_cached_script_path(script_id)
        
        if cached_path:
            pass  # removed debug log
            return cached_path
        
        # No bundled fallback per requirements
        pass  # removed debug log
        return None
    
    def get_script_status(self, filename) -> str:
        """Get status of a script (cached, outdated, not_installed)"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            pass  # removed debug log
            return "unknown"
        
        category = script.get('category')
        remote_checksum = script.get('checksum', '').replace('sha256:', '')
        
        if not all([category, filename]):
            return "unknown"
        
        # Type narrowing: assert category and filename are not None
        assert category is not None and filename is not None
        
        cached_path = self.script_cache_dir / category / filename
        
        if cached_path.exists():
            local_checksum: str = self._calculate_checksum(str(cached_path))
            
            status: str = "cached" if local_checksum == remote_checksum else "outdated"
            pass  # removed debug log
            return status
        else:
            pass  # removed debug log
            return "not_installed"
    
    def get_script_version(self, filename):
        """Get version of a script"""
        script = self.get_script_by_filename(filename)
        
        if not script:
            return "unknown"
        
        return script.get('version', 'unknown')
    
    def download_all_scripts(self) -> Tuple[int, int]:
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
        pass  # removed debug log
        return downloaded, failed
    def remove_cached_script(self, script_id: str) -> bool:
        """Remove a cached script"""
        script = self.get_script_by_id(script_id)
        if not script:
            return False
        
        category = script.get('category')
        filename = script.get('file_name')
        
        if not category or not filename:
            return False
        
        cached_path = self.script_cache_dir / category / filename
        try:
            if cached_path.exists():
                cached_path.unlink()
                logging.info(f"Removed cached script: {script_id}")
                return True
        except Exception as e:
            logging.error(f"Failed to remove cached script {script_id}: {e}")
        
        return False


# ============================================================================
# REPOSITORY OPERATIONS - High-level wrappers with terminal feedback
# ============================================================================

def download_script_with_feedback(
    repository: 'ScriptRepository',
    script_id: str,
    script_name: str,
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[bool, Optional[str]]:
    """Download a script with terminal feedback"""
    if not repository:
        return False, None
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[33m[*] Downloading {script_name} to cache...\x1b[0m\r\n".encode())
        
        if manifest_path:
            terminal_widget.feed(f"\x1b[36m[DEBUG] Using custom manifest: {manifest_path}\x1b[0m\r\n".encode())
        terminal_widget.feed(f"\x1b[36m[DEBUG] Script ID: {script_id}\x1b[0m\r\n".encode())
    
    try:
        result = repository.download_script(script_id, manifest_path=manifest_path)
        success = result[0] if isinstance(result, tuple) else result
        url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
        
        if success:
            if terminal_widget:
                if url:
                    terminal_widget.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                terminal_widget.feed(f"\x1b[32m[✓] Successfully downloaded {script_name}\x1b[0m\r\n".encode())
            
            # Get cached path
            cached_path: str | None = repository.get_cached_script_path(script_id)
            return True, cached_path
        else:
            if terminal_widget:
                if url:
                    terminal_widget.feed(f"\x1b[33m[!] Attempted URL: {url}\x1b[0m\r\n".encode())
                terminal_widget.feed(f"\x1b[31m[✗] Failed to download {script_name}\x1b[0m\r\n".encode())
                terminal_widget.feed(f"\x1b[33m[!] Check ~/.lv_linux_learn/logs/repository.log for details\x1b[0m\r\n".encode())
            return False, None
            
    except Exception as e:
        if terminal_widget:
            if "Checksum verification failed" in str(e):
                terminal_widget.feed(f"\x1b[31m[✗] Checksum verification failed for {script_name}\x1b[0m\r\n".encode())
                terminal_widget.feed(f"\x1b[33m[!] Script may have been updated since manifest was generated\x1b[0m\r\n".encode())
            else:
                terminal_widget.feed(f"\x1b[31m[✗] Error downloading {script_name}: {e}\x1b[0m\r\n".encode())
        return False, None


def update_script_with_feedback(
    repository: 'ScriptRepository',
    script_id: str,
    script_name: str,
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> bool:
    """Update a cached script with terminal feedback"""
    if not repository:
        return False
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[33m[*] Updating {script_name}...\x1b[0m\r\n".encode())
    
    try:
        result = repository.download_script(script_id, manifest_path=manifest_path)
        success = result[0] if isinstance(result, tuple) else result
        
        if success:
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m[✓] Successfully updated {script_name}\x1b[0m\r\n".encode())
            return True
        else:
            if terminal_widget:
                terminal_widget.feed(f"\x1b[31m[✗] Failed to update {script_name}\x1b[0m\r\n".encode())
            return False
            
    except Exception as e:
        if terminal_widget:
            if "Checksum verification failed" in str(e):
                terminal_widget.feed(f"\x1b[31m[✗] Checksum verification failed\x1b[0m\r\n".encode())
                terminal_widget.feed(f"\x1b[33m[!] Remote file may have changed. Check manifest checksums.\x1b[0m\r\n".encode())
            else:
                terminal_widget.feed(f"\x1b[31m[✗] Error updating {script_name}: {e}\x1b[0m\r\n".encode())
        return False


def remove_script_with_feedback(
    repository: 'ScriptRepository',
    script_id: str,
    script_name: str,
    terminal_widget=None
) -> bool:
    """Remove a cached script with terminal feedback"""
    if not repository:
        return False
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[33m[*] Removing {script_name} from cache...\x1b[0m\r\n".encode())
    
    try:
        success: bool = repository.remove_cached_script(script_id)
        
        if success:
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m[✓] Successfully removed {script_name}\x1b[0m\r\n".encode())
            return True
        else:
            if terminal_widget:
                terminal_widget.feed(f"\x1b[33m[!] Script not found in cache: {script_name}\x1b[0m\r\n".encode())
            return False
            
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        return False


def download_all_scripts_with_feedback(
    repository: 'ScriptRepository',
    script_list: List[Tuple[str, str]],
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[int, int]:
    """Download multiple scripts with progress feedback"""
    if not repository or not script_list:
        return 0, 0
    
    total: int = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Downloading {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success, _ = download_script_with_feedback(
            repository, script_id, script_name, manifest_path, None
        )
        
        if success:
            successful += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m  ✓ Downloaded\x1b[0m\r\n".encode())
        else:
            failed += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[31m  ✗ Failed\x1b[0m\r\n".encode())
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Download complete: {successful} successful, {failed} failed\x1b[0m\r\n".encode())
    
    return successful, failed


def update_all_scripts_with_feedback(
    repository: 'ScriptRepository',
    script_list: List[Tuple[str, str]],
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[int, int]:
    """Update multiple scripts with progress feedback"""
    if not repository or not script_list:
        return 0, 0
    
    total: int = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Updating {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success: bool = update_script_with_feedback(
            repository, script_id, script_name, manifest_path, None
        )
        
        if success:
            successful += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m  ✓ Updated\x1b[0m\r\n".encode())
        else:
            failed += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[31m  ✗ Failed\x1b[0m\r\n".encode())
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Update complete: {successful} successful, {failed} failed\x1b[0m\r\n".encode())
    
    return successful, failed


def remove_all_scripts_with_feedback(
    repository: 'ScriptRepository',
    script_list: List[Tuple[str, str]],
    terminal_widget=None
) -> Tuple[int, int]:
    """Remove multiple scripts with progress feedback"""
    if not repository or not script_list:
        return 0, 0
    
    total: int = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Removing {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success: bool = remove_script_with_feedback(
            repository, script_id, script_name, None
        )
        
        if success:
            successful += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m  ✓ Removed\x1b[0m\r\n".encode())
        else:
            failed += 1
            if terminal_widget:
                terminal_widget.feed(f"\x1b[31m  ✗ Not found\x1b[0m\r\n".encode())
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Removal complete: {successful} removed, {failed} not found\x1b[0m\r\n".encode())
    
    return successful, failed


def clear_cache_with_feedback(
    repository: 'ScriptRepository',
    terminal_widget=None
) -> bool:
    """Clear entire script cache with terminal feedback"""
    if not repository:
        return False
    
    if terminal_widget:
        terminal_widget.feed("\r\n\x1b[33m[*] Clearing script cache...\x1b[0m\r\n".encode())
    
    try:
        success: bool = repository.clear_cache()
        
        if success:
            if terminal_widget:
                terminal_widget.feed("\x1b[32m[✓] Cache cleared successfully\x1b[0m\r\n".encode())
            return True
        else:
            if terminal_widget:
                terminal_widget.feed("\x1b[33m[!] Cache was already empty\x1b[0m\r\n".encode())
            return False
            
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"\x1b[31m[✗] Error clearing cache: {e}\x1b[0m\r\n".encode())
        return False


def get_cache_stats(repository: 'ScriptRepository') -> dict:
    """Get cache statistics"""
    if not repository:
        return {'total_scripts': 0, 'total_size_bytes': 0, 'categories': {}}
    
    cache_dir: Path = repository.script_cache_dir
    stats = {
        'total_scripts': 0,
        'total_size_bytes': 0,
        'categories': {}
    }
    
    if not cache_dir.exists():
        return stats
    
    # Scan cache directory
    for category_dir in cache_dir.iterdir():
        if category_dir.is_dir() and category_dir.name != 'includes':
            category_stats: dict[str, int] = {
                'count': 0,
                'size': 0
            }
            
            for script_file in category_dir.glob('*.sh'):
                if script_file.is_file():
                    size: int = script_file.stat().st_size
                    category_stats['count'] += 1
                    category_stats['size'] += size
                    stats['total_scripts'] += 1
                    stats['total_size_bytes'] += size
            
            if category_stats['count'] > 0:
                stats['categories'][category_dir.name] = category_stats
    
    return stats