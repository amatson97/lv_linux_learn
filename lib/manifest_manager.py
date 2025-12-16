"""
Manifest Manager Module
Handles AI-powered manifest updates and script reorganization
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ManifestManager:
    """
    Manages local repository manifests with AI-powered categorization
    """
    
    def __init__(self, manifest_path: str):
        """
        Initialize manifest manager
        
        Args:
            manifest_path: Path to the manifest.json file
        """
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
        """
        Update a script's metadata based on AI analysis results
        
        Args:
            script_id: Script ID to update
            analysis: AI analysis dict with category, description, dependencies, safety
            
        Returns:
            True if updated successfully
        """
        if not self.manifest_data:
            return False
        
        # Find the script in the manifest
        scripts = self.manifest_data.get('scripts', {})
        
        # Handle both nested dict and flat list structures
        script_found = False
        old_category = None
        
        if isinstance(scripts, dict):
            # Nested structure: {"category": [scripts]}
            for category, category_scripts in scripts.items():
                if isinstance(category_scripts, list):
                    for script in category_scripts:
                        if script.get('id') == script_id:
                            # Found the script
                            old_category = category
                            new_category = analysis.get('category', 'tools')
                            
                            # Map 'custom' to 'tools' - custom category is deprecated
                            if new_category == 'custom':
                                new_category = 'tools'
                            
                            # Update script metadata
                            script['category'] = new_category
                            script['description'] = analysis.get('description', script.get('description', ''))
                            
                            # Add AI-specific fields
                            if 'dependencies' in analysis and analysis['dependencies']:
                                script['dependencies'] = analysis['dependencies']
                            if 'safety' in analysis:
                                script['safety'] = analysis['safety']
                            if 'purpose' in analysis:
                                script['purpose'] = analysis['purpose']
                            
                            # If category changed, move the script
                            if new_category != old_category:
                                # Remove from old category
                                category_scripts.remove(script)
                                
                                # Add to new category
                                if new_category not in scripts:
                                    scripts[new_category] = []
                                scripts[new_category].append(script)
                            
                            script_found = True
                            break
                
                if script_found:
                    break
        else:
            # Flat structure: [scripts]
            for script in scripts:
                if script.get('id') == script_id:
                    old_category = script.get('category', 'tools')
                    new_category = analysis.get('category', 'tools')
                    
                    # Map 'custom' to 'tools' - custom category is deprecated
                    if new_category == 'custom':
                        new_category = 'tools'
                    
                    # Update script metadata
                    script['category'] = new_category
                    script['description'] = analysis.get('description', script.get('description', ''))
                    
                    # Add AI-specific fields
                    if 'dependencies' in analysis and analysis['dependencies']:
                        script['dependencies'] = analysis['dependencies']
                    if 'safety' in analysis:
                        script['safety'] = analysis['safety']
                    if 'purpose' in analysis:
                        script['purpose'] = analysis['purpose']
                    
                    script_found = True
                    break
        
        if script_found:
            # Save the updated manifest
            return self.save_manifest()
        
        return False
    
    def batch_update_scripts(self, updates: Dict[str, Dict]) -> Dict[str, bool]:
        """
        Update multiple scripts from AI analysis
        
        Args:
            updates: Dict mapping script_id -> analysis_dict
            
        Returns:
            Dict mapping script_id -> success_bool
        """
        results = {}
        
        for script_id, analysis in updates.items():
            if 'error' not in analysis:
                success = self.update_script_from_ai_analysis(script_id, analysis)
                results[script_id] = success
            else:
                results[script_id] = False
        
        return results
    
    def reorganize_by_category(self) -> bool:
        """
        Reorganize manifest scripts into nested category structure
        
        Converts flat list to nested dict: {"category": [scripts]}
        """
        if not self.manifest_data:
            return False
        
        scripts = self.manifest_data.get('scripts', [])
        
        # If already nested, skip
        if isinstance(scripts, dict):
            return True
        
        # Reorganize into nested structure
        categorized = {}
        
        for script in scripts:
            category = script.get('category', 'custom')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(script)
        
        # Update manifest
        self.manifest_data['scripts'] = categorized
        
        return self.save_manifest()
    
    def get_script_by_id(self, script_id: str) -> Optional[Dict]:
        """
        Find a script by ID
        
        Args:
            script_id: Script ID to find
            
        Returns:
            Script dict or None if not found
        """
        if not self.manifest_data:
            return None
        
        scripts = self.manifest_data.get('scripts', {})
        
        if isinstance(scripts, dict):
            # Nested structure
            for category_scripts in scripts.values():
                if isinstance(category_scripts, list):
                    for script in category_scripts:
                        if script.get('id') == script_id:
                            return script
        else:
            # Flat structure
            for script in scripts:
                if script.get('id') == script_id:
                    return script
        
        return None
    
    def add_script(self, script_data: Dict) -> bool:
        """
        Add a new script to the manifest
        
        Args:
            script_data: Script metadata dict
            
        Returns:
            True if added successfully
        """
        if not self.manifest_data:
            self.manifest_data = {
                'version': '1.0.0',
                'repository_url': '',
                'scripts': {}
            }
        
        category = script_data.get('category', 'custom')
        scripts = self.manifest_data.get('scripts', {})
        
        # Ensure nested structure
        if not isinstance(scripts, dict):
            # Convert to nested
            self.manifest_data['scripts'] = {}
            scripts = self.manifest_data['scripts']
        
        # Add to category
        if category not in scripts:
            scripts[category] = []
        
        scripts[category].append(script_data)
        
        return self.save_manifest()


def get_local_repository_manifests() -> List[Path]:
    """
    Get list of all local repository manifest files
    
    Returns:
        List of Path objects to manifest.json files
    """
    manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
    
    if not manifests_dir.exists():
        return []
    
    return list(manifests_dir.glob('*/manifest.json'))


def update_manifest_from_ai_batch(analysis_results: Dict[str, tuple]) -> Dict[str, str]:
    """
    Update local repository manifests based on AI analysis results
    
    Args:
        analysis_results: Dict mapping script_id -> (script_name, analysis_dict, manifest_path)
        
    Returns:
        Dict mapping script_id -> status_message
    """
    results = {}
    
    # Group by manifest path
    by_manifest = {}
    for script_id, (script_name, analysis, manifest_path) in analysis_results.items():
        if manifest_path not in by_manifest:
            by_manifest[manifest_path] = []
        by_manifest[manifest_path].append((script_id, script_name, analysis))
    
    # Update each manifest
    for manifest_path, scripts in by_manifest.items():
        try:
            manager = ManifestManager(manifest_path)
            
            for script_id, script_name, analysis in scripts:
                if 'error' in analysis:
                    results[script_id] = f"Skipped: {analysis['error']}"
                    continue
                
                success = manager.update_script_from_ai_analysis(script_id, analysis)
                
                if success:
                    new_category = analysis.get('category', 'custom')
                    results[script_id] = f"Updated: moved to '{new_category}'"
                else:
                    results[script_id] = "Failed: could not update manifest"
        
        except Exception as e:
            for script_id, script_name, _ in scripts:
                results[script_id] = f"Error: {e}"
    
    return results
