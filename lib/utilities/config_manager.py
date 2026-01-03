"""
ConfigManager - Centralized configuration management

Eliminates 14+ duplicate config loading calls throughout the codebase
"""
import time
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Centralized configuration management with caching
    
    Provides consistent access to repository configuration with optional caching
    to reduce redundant disk reads.
    """
    
    def __init__(self, repository):
        """
        Initialize ConfigManager
        
        Args:
            repository: Repository instance with load_config() method
        """
        self.repository = repository
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl: float = 5.0  # Cache valid for 5 seconds
    
    def get_config(self, force_reload: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get configuration with optional caching
        
        Args:
            force_reload: Force reload from disk even if cache is valid
            use_cache: Use cache if available and valid
            
        Returns:
            Configuration dictionary
        """
        current_time = time.time()
        
        # Check if cache is valid
        cache_valid = (
            use_cache and 
            self._cache is not None and 
            self._cache_timestamp is not None and
            (current_time - self._cache_timestamp) < self._cache_ttl
        )
        
        if force_reload or not cache_valid:
            self._cache = self.repository.load_config() if self.repository else {}
            self._cache_timestamp = current_time
        
        return self._cache or {}
    
    def reload(self) -> Dict[str, Any]:
        """
        Force configuration reload
        
        Returns:
            Reloaded configuration dictionary
        """
        return self.get_config(force_reload=True)
    
    def get_custom_manifests(self) -> Dict[str, Any]:
        """
        Get custom manifests configuration
        
        Returns:
            Custom manifests dictionary
        """
        return self.get_config().get('custom_manifests', {})
    
    def is_public_repo_enabled(self) -> bool:
        """
        Check if public repository is enabled
        
        Returns:
            True if public repository is enabled
        """
        return self.get_config().get('use_public_repository', True)
    
    def get_custom_manifest_url(self) -> Optional[str]:
        """
        Get custom manifest URL if configured
        
        Returns:
            Custom manifest URL or None
        """
        return self.get_config().get('custom_manifest_url')
    
    def get_active_custom_manifest(self) -> Optional[str]:
        """
        Get active custom manifest name
        
        Returns:
            Active manifest name or None
        """
        return self.get_config().get('active_custom_manifest')
    
    def invalidate_cache(self):
        """Invalidate the cache, forcing next read to reload from disk"""
        self._cache = None
        self._cache_timestamp = None
