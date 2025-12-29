"""
Repository Service Module
Consolidated entry point for repository operations.
Wraps ScriptRepository and feedback helpers (from repository_ops) under one module.
"""

from typing import Optional, Tuple, List
import os

try:
    from lib.repository import ScriptRepository, ChecksumVerificationError
except ImportError:
    ScriptRepository = None  # type: ignore
    class ChecksumVerificationError(Exception):
        pass

try:
    from lib import repository_ops as _ops
except ImportError:
    _ops = None

# ---------------------------------------------------------------------------
# Feedback wrappers (fallback implementations included)
# ---------------------------------------------------------------------------

def download_script_with_feedback(
    repository: 'ScriptRepository',
    script_id: str,
    script_name: str,
    manifest_path: Optional[str] = None,
    terminal_widget=None
) -> Tuple[bool, Optional[str]]:
    if _ops:
        return _ops.download_script_with_feedback(repository, script_id, script_name, manifest_path, terminal_widget)
    # Fallback: minimal implementation
    if not repository:
        return False, None
    try:
        result = repository.download_script(script_id, manifest_path=manifest_path)
        success = result[0] if isinstance(result, tuple) else bool(result)
        if success:
            cached = repository.get_cached_script_path(script_id)
            if terminal_widget:
                terminal_widget.feed(f"\x1b[32m[✓] Successfully downloaded {script_name}\x1b[0m\r\n".encode())
            return True, cached
        else:
            if terminal_widget:
                terminal_widget.feed(f"\x1b[31m[✗] Failed to download {script_name}\x1b[0m\r\n".encode())
            return False, None
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"\x1b[31m[✗] Error downloading {script_name}: {e}\x1b[0m\r\n".encode())
        return False, None

def update_script_with_feedback(repository, script_id, script_name, manifest_path=None, terminal_widget=None) -> bool:
    if _ops:
        return _ops.update_script_with_feedback(repository, script_id, script_name, manifest_path, terminal_widget)
    # Fallback
    ok, _ = download_script_with_feedback(repository, script_id, script_name, manifest_path, terminal_widget)
    return ok

def remove_script_with_feedback(repository, script_id, script_name, terminal_widget=None) -> bool:
    if _ops:
        return _ops.remove_script_with_feedback(repository, script_id, script_name, terminal_widget)
    if not repository:
        return False
    try:
        success = repository.remove_cached_script(script_id)
        if terminal_widget:
            if success:
                terminal_widget.feed(f"\x1b[32m[✓] Successfully removed {script_name}\x1b[0m\r\n".encode())
            else:
                terminal_widget.feed(f"\x1b[33m[!] Script not found in cache: {script_name}\x1b[0m\r\n".encode())
        return success
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        return False

def download_all_scripts_with_feedback(repository, script_list: List[Tuple[str, str]], manifest_path=None, terminal_widget=None) -> Tuple[int,int]:
    if _ops:
        return _ops.download_all_scripts_with_feedback(repository, script_list, manifest_path, terminal_widget)
    if not repository or not script_list:
        return 0,0
    success = 0
    failed = 0
    for script_id, script_name in script_list:
        ok, _ = download_script_with_feedback(repository, script_id, script_name, manifest_path, terminal_widget)
        if ok:
            success +=1
        else:
            failed +=1
    return success, failed

def update_all_scripts_with_feedback(repository, script_list: List[Tuple[str, str]], manifest_path=None, terminal_widget=None) -> Tuple[int,int]:
    if _ops:
        return _ops.update_all_scripts_with_feedback(repository, script_list, manifest_path, terminal_widget)
    if not repository or not script_list:
        return 0,0
    success = 0
    failed = 0
    for script_id, script_name in script_list:
        ok = update_script_with_feedback(repository, script_id, script_name, manifest_path, terminal_widget)
        if ok:
            success +=1
        else:
            failed +=1
    return success, failed

def remove_all_scripts_with_feedback(repository, script_list: List[Tuple[str, str]], terminal_widget=None) -> Tuple[int,int]:
    if _ops:
        return _ops.remove_all_scripts_with_feedback(repository, script_list, terminal_widget)
    if not repository or not script_list:
        return 0,0
    success = 0
    failed = 0
    for script_id, script_name in script_list:
        ok = remove_script_with_feedback(repository, script_id, script_name, terminal_widget)
        if ok:
            success +=1
        else:
            failed +=1
    return success, failed

def clear_cache_with_feedback(repository, terminal_widget=None) -> bool:
    if _ops:
        return _ops.clear_cache_with_feedback(repository, terminal_widget)
    if not repository:
        return False
    try:
        repository.clear_cache()
        if terminal_widget:
            terminal_widget.feed("\x1b[32m[✓] Cache cleared successfully\x1b[0m\r\n".encode())
        return True
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"\x1b[31m[✗] Error clearing cache: {e}\x1b[0m\r\n".encode())
        return False

def get_cache_stats(repository) -> Tuple[int, int]:
    if _ops:
        return _ops.get_cache_stats(repository)
    if not repository:
        return 0,0
    try:
        total_cached = sum(1 for _ in repository.script_cache_dir.glob('**/*.sh'))
        total_categories = len([p for p in repository.script_cache_dir.iterdir() if p.is_dir()]) if repository.script_cache_dir.exists() else 0
        return total_cached, total_categories
    except Exception:
        return 0,0

__all__ = [
    'ScriptRepository',
    'ChecksumVerificationError',
    'download_script_with_feedback',
    'update_script_with_feedback',
    'remove_script_with_feedback',
    'download_all_scripts_with_feedback',
    'update_all_scripts_with_feedback',
    'remove_all_scripts_with_feedback',
    'clear_cache_with_feedback',
    'get_cache_stats',
]
