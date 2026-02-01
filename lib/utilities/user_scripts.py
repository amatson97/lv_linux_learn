#!/usr/bin/env python3
"""
User Script Manager Module (renamed from custom_scripts.py)
Manages user-created custom scripts for lv_linux_learn
"""

import json
import uuid
from pathlib import Path
from datetime import datetime


class CustomScriptManager:
    """Manages user-created custom scripts"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.lv_linux_learn'
        self.scripts_dir = self.config_dir / 'scripts'
        self.config_file = self.config_dir / 'custom_scripts.json'
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create config directories if they don't exist"""
        self.config_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self._save_config({"scripts": []})
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load custom scripts config: {e}")
            return {"scripts": []}
    
    def _save_config(self, config):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save custom scripts config: {e}")
    
    def add_script(self, name, description, content):
        """Add a new custom script"""
        config = self._load_config()
        scripts = config.get('scripts', [])
        
        script_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        script_path = self.scripts_dir / f"{script_id}.sh"
        with open(script_path, 'w') as f:
            f.write(content)
        script_path.chmod(0o755)
        
        scripts.append({
            "id": script_id,
            "name": name,
            "description": description,
            "path": str(script_path),
            "created": timestamp
        })
        
        config['scripts'] = scripts
        self._save_config(config)
        
        return script_id, script_path
    
    def list_scripts(self):
        """List all custom scripts"""
        config = self._load_config()
        return config.get('scripts', [])
    
    def get_scripts(self, category=None):
        """
        Get custom scripts with optional category filtering
        
        Args:
            category: Optional category filter (not used for custom scripts but kept for API compatibility)
            
        Returns:
            List of custom scripts
        """
        return self.list_scripts()
    
    def get_script_by_id(self, script_id):
        """Get a custom script by ID"""
        config = self._load_config()
        scripts = config.get('scripts', [])
        
        for script in scripts:
            if script.get('id') == script_id:
                return script
        
        return None
    
    def update_script(self, script_id, name=None, description=None, content=None):
        """Update an existing custom script"""
        config = self._load_config()
        scripts = config.get('scripts', [])
        
        for script in scripts:
            if script.get('id') == script_id:
                # Update metadata
                if name is not None:
                    script['name'] = name
                if description is not None:
                    script['description'] = description
                
                # Update script content if provided
                if content is not None:
                    script_path = Path(script.get('path'))
                    if script_path.exists():
                        with open(script_path, 'w') as f:
                            f.write(content)
                        script_path.chmod(0o755)
                
                script['modified'] = datetime.now().isoformat()
                config['scripts'] = scripts
                self._save_config(config)
                return True
        
        return False
    
    def delete_script(self, script_id):
        """Delete a custom script by ID (alias for remove_script)"""
        return self.remove_script(script_id)
    
    def remove_script(self, script_id):
        """Remove a custom script by ID"""
        config = self._load_config()
        scripts = config.get('scripts', [])
        
        new_scripts = [s for s in scripts if s.get('id') != script_id]
        removed = len(new_scripts) != len(scripts)
        
        if removed:
            # Delete script file
            for s in scripts:
                if s.get('id') == script_id:
                    script_path = s.get('path')
                    if script_path and Path(script_path).exists():
                        Path(script_path).unlink(missing_ok=True)
                    break
            
            config['scripts'] = new_scripts
            self._save_config(config)
        
        return removed
