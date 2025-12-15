"""
Repository Operations Module
High-level wrappers for repository operations with terminal feedback
"""

from pathlib import Path
from typing import Optional, Tuple, List
import os

try:
    from lib.repository import ScriptRepository
except ImportError:
    ScriptRepository = None


# ============================================================================
# SCRIPT DOWNLOAD OPERATIONS
# ============================================================================

def download_script_with_feedback(
    repository: 'ScriptRepository',
    script_id: str,
    script_name: str,
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[bool, Optional[str]]:
    """
    Download a script with terminal feedback
    
    Args:
        repository: ScriptRepository instance
        script_id: Script ID to download
        script_name: Display name for terminal output
        manifest_path: Optional path to custom manifest
        terminal_widget: Optional terminal for output
        
    Returns:
        Tuple of (success: bool, cached_path: str or None)
    """
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
            cached_path = repository.get_cached_script_path(script_id)
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
    """
    Force update a cached script with terminal feedback
    
    Args:
        repository: ScriptRepository instance
        script_id: Script ID to update
        script_name: Display name for terminal output
        manifest_path: Optional path to custom manifest
        terminal_widget: Optional terminal for output
        
    Returns:
        True if successful, False otherwise
    """
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
    """
    Remove a cached script with terminal feedback
    
    Args:
        repository: ScriptRepository instance
        script_id: Script ID to remove
        script_name: Display name for terminal output
        terminal_widget: Optional terminal for output
        
    Returns:
        True if successful, False otherwise
    """
    if not repository:
        return False
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[33m[*] Removing {script_name} from cache...\x1b[0m\r\n".encode())
    
    try:
        success = repository.remove_cached_script(script_id)
        
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


# ============================================================================
# BULK OPERATIONS
# ============================================================================

def download_all_scripts_with_feedback(
    repository: 'ScriptRepository',
    script_list: List[Tuple[str, str]],  # List of (script_id, script_name) tuples
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[int, int]:
    """
    Download multiple scripts with progress feedback
    
    Args:
        repository: ScriptRepository instance
        script_list: List of (script_id, script_name) tuples
        manifest_path: Optional path to custom manifest
        terminal_widget: Optional terminal for output
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not repository or not script_list:
        return 0, 0
    
    total = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Downloading {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success, _ = download_script_with_feedback(
            repository, script_id, script_name, manifest_path, None  # Don't pass terminal to avoid duplicate output
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
    script_list: List[Tuple[str, str]],  # List of (script_id, script_name) tuples
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[int, int]:
    """
    Update multiple scripts with progress feedback
    
    Args:
        repository: ScriptRepository instance
        script_list: List of (script_id, script_name) tuples
        manifest_path: Optional path to custom manifest
        terminal_widget: Optional terminal for output
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not repository or not script_list:
        return 0, 0
    
    total = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Updating {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success = update_script_with_feedback(
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
    script_list: List[Tuple[str, str]],  # List of (script_id, script_name) tuples
    terminal_widget=None
) -> Tuple[int, int]:
    """
    Remove multiple scripts with progress feedback
    
    Args:
        repository: ScriptRepository instance
        script_list: List of (script_id, script_name) tuples
        terminal_widget: Optional terminal for output
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not repository or not script_list:
        return 0, 0
    
    total = len(script_list)
    successful = 0
    failed = 0
    
    if terminal_widget:
        terminal_widget.feed(f"\r\n\x1b[36m[*] Removing {total} script(s)...\x1b[0m\r\n".encode())
    
    for idx, (script_id, script_name) in enumerate(script_list, 1):
        if terminal_widget:
            terminal_widget.feed(f"\x1b[33m[{idx}/{total}] {script_name}...\x1b[0m\r\n".encode())
        
        success = remove_script_with_feedback(
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


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_cache_with_feedback(
    repository: 'ScriptRepository',
    terminal_widget=None
) -> bool:
    """
    Clear entire script cache with terminal feedback
    
    Args:
        repository: ScriptRepository instance
        terminal_widget: Optional terminal for output
        
    Returns:
        True if successful, False otherwise
    """
    if not repository:
        return False
    
    if terminal_widget:
        terminal_widget.feed("\r\n\x1b[33m[*] Clearing script cache...\x1b[0m\r\n".encode())
    
    try:
        success = repository.clear_cache()
        
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
    """
    Get cache statistics
    
    Args:
        repository: ScriptRepository instance
        
    Returns:
        Dictionary with cache stats: {
            'total_scripts': int,
            'total_size_bytes': int,
            'categories': dict
        }
    """
    if not repository:
        return {'total_scripts': 0, 'total_size_bytes': 0, 'categories': {}}
    
    cache_dir = repository.script_cache_dir
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
            category_stats = {
                'count': 0,
                'size': 0
            }
            
            for script_file in category_dir.glob('*.sh'):
                if script_file.is_file():
                    size = script_file.stat().st_size
                    category_stats['count'] += 1
                    category_stats['size'] += size
                    stats['total_scripts'] += 1
                    stats['total_size_bytes'] += size
            
            if category_stats['count'] > 0:
                stats['categories'][category_dir.name] = category_stats
    
    return stats
