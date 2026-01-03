"""
FileLoader - Centralized file loading with consistent error handling

Eliminates 14+ duplicate JSON loading patterns throughout the codebase
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class FileLoader:
    """
    Centralized file loading utilities with consistent error handling
    
    Provides safe JSON loading/saving with automatic error handling and
    sensible defaults.
    """
    
    @staticmethod
    def load_json(
        file_path: Union[str, Path], 
        default: Optional[Any] = None,
        silent: bool = False
    ) -> Any:
        """
        Load JSON file with error handling
        
        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or fails to load
            silent: If True, suppress error messages
        
        Returns:
            Loaded JSON data or default value (empty dict if default is None)
        """
        try:
            if not isinstance(file_path, Path):
                file_path = Path(file_path)
            
            if not file_path.exists():
                return default if default is not None else {}
            
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            if not silent:
                print(f"JSON decode error in {file_path}: {e}")
            return default if default is not None else {}
        except Exception as e:
            if not silent:
                print(f"Error loading {file_path}: {e}")
            return default if default is not None else {}
    
    @staticmethod
    def save_json(
        file_path: Union[str, Path], 
        data: Any, 
        indent: int = 2,
        ensure_parents: bool = True,
        silent: bool = False
    ) -> bool:
        """
        Save data as JSON file
        
        Args:
            file_path: Path to save JSON file
            data: Data to save (must be JSON serializable)
            indent: Indentation level (None for compact)
            ensure_parents: Create parent directories if needed
            silent: If True, suppress error messages
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not isinstance(file_path, Path):
                file_path = Path(file_path)
            
            if ensure_parents:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=indent)
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"Error saving {file_path}: {e}")
            return False
    
    @staticmethod
    def load_text(
        file_path: Union[str, Path],
        default: str = "",
        silent: bool = False
    ) -> str:
        """
        Load text file with error handling
        
        Args:
            file_path: Path to text file
            default: Default value if file doesn't exist or fails to load
            silent: If True, suppress error messages
        
        Returns:
            File contents or default value
        """
        try:
            if not isinstance(file_path, Path):
                file_path = Path(file_path)
            
            if not file_path.exists():
                return default
            
            with open(file_path, 'r') as f:
                return f.read()
                
        except Exception as e:
            if not silent:
                print(f"Error loading {file_path}: {e}")
            return default
    
    @staticmethod
    def save_text(
        file_path: Union[str, Path],
        content: str,
        ensure_parents: bool = True,
        silent: bool = False
    ) -> bool:
        """
        Save text to file
        
        Args:
            file_path: Path to save text file
            content: Text content to save
            ensure_parents: Create parent directories if needed
            silent: If True, suppress error messages
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not isinstance(file_path, Path):
                file_path = Path(file_path)
            
            if ensure_parents:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            if not silent:
                print(f"Error saving {file_path}: {e}")
            return False
