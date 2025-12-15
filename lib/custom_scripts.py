#!/usr/bin/env python3
"""
Custom Script Manager Module
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
            return True
        except Exception as e:
            print(f"Error: Failed to save custom scripts config: {e}")
            return False
    
    def get_scripts(self, category=None):
        """Get all custom scripts, optionally filtered by category"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        if category:
            scripts = [s for s in scripts if s.get("category") == category]
        return scripts
    
    def add_script(self, name, category, script_path, description, requires_sudo=True):
        """Add a new custom script"""
        config = self._load_config()
        
        script_obj = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "script_path": str(script_path),
            "description": description,
            "requires_sudo": requires_sudo,
            "created_date": datetime.now().isoformat(),
            "is_custom": True
        }
        
        config["scripts"].append(script_obj)
        return self._save_config(config)
    
    def update_script(self, script_id, **kwargs):
        """Update an existing custom script"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        
        for script in scripts:
            if script.get("id") == script_id:
                script.update(kwargs)
                return self._save_config(config)
        return False
    
    def delete_script(self, script_id):
        """Delete a custom script"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        
        config["scripts"] = [s for s in scripts if s.get("id") != script_id]
        return self._save_config(config)
    
    def get_script_by_id(self, script_id):
        """Get a single script by ID"""
        scripts = self.get_scripts()
        for script in scripts:
            if script.get("id") == script_id:
                return script
        return None
