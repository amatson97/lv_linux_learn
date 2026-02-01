"""
PathManager - Centralized path management for application directories

Eliminates 17+ duplicate path constructions throughout the codebase
"""
from pathlib import Path
from typing import Optional

try:
    from lib import config as C
except ImportError:
    C = None


class PathManager:
    """Centralized path management for all application directories and files"""
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get main config directory (~/.lv_linux_learn)"""
        return C.CONFIG_DIR if C else Path.home() / '.lv_linux_learn'
    
    @staticmethod
    def get_custom_manifests_dir() -> Path:
        """Get custom manifests directory"""
        return PathManager.get_config_dir() / 'custom_manifests'
    
    @staticmethod
    def get_config_file() -> Path:
        """Get config.json path"""
        return C.CONFIG_FILE if C else PathManager.get_config_dir() / 'config.json'
    
    @staticmethod
    def get_cache_dir() -> Path:
        """Get script cache directory"""
        return C.SCRIPT_CACHE_DIR if C else PathManager.get_config_dir() / 'script_cache'
    
    @staticmethod
    def get_manifest_cache_file() -> Path:
        """Get manifest cache file path"""
        return C.MANIFEST_CACHE_FILE if C else PathManager.get_config_dir() / 'manifest.json'
    
    @staticmethod
    def get_ui_state_file() -> Path:
        """Get UI state file path"""
        return C.UI_STATE_FILE if C else PathManager.get_config_dir() / 'ui_state.json'
    
    @staticmethod
    def get_custom_scripts_file() -> Path:
        """Get custom scripts file path"""
        return C.CUSTOM_SCRIPTS_FILE if C else PathManager.get_config_dir() / 'custom_scripts.json'
    
    @staticmethod
    def get_manifest_for_repo(repo_name: str) -> Path:
        """
        Get manifest path for a specific repository
        
        Args:
            repo_name: Repository name
            
        Returns:
            Path to repository's manifest.json
        """
        return PathManager.get_custom_manifests_dir() / repo_name / 'manifest.json'
    
    @staticmethod
    def get_repo_manifest_dir(repo_name: str) -> Path:
        """
        Get repository manifest directory
        
        Args:
            repo_name: Repository name
            
        Returns:
            Path to repository directory
        """
        return PathManager.get_custom_manifests_dir() / repo_name
    
    @staticmethod
    def is_in_custom_manifests(path: Path) -> bool:
        """
        Check if path is within custom_manifests directory
        
        Args:
            path: Path to check
            
        Returns:
            True if path is under custom_manifests
        """
        try:
            custom_root: Path = PathManager.get_custom_manifests_dir()
            return custom_root in path.parents or path == custom_root
        except Exception:
            return False
    
    @staticmethod
    def ensure_config_dir_exists() -> Path:
        """
        Ensure config directory exists, create if needed
        
        Returns:
            Path to config directory
        """
        config_dir: Path = PathManager.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @staticmethod
    def ensure_custom_manifests_dir_exists() -> Path:
        """
        Ensure custom manifests directory exists, create if needed
        
        Returns:
            Path to custom manifests directory
        """
        manifests_dir: Path = PathManager.get_custom_manifests_dir()
        manifests_dir.mkdir(parents=True, exist_ok=True)
        return manifests_dir
