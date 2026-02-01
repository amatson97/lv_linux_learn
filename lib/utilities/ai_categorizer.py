"""
AI Script Categorizer Module (renamed from ai_analyzer.py)
Uses Ollama for local AI-powered script analysis
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List


class OllamaAnalyzer:
    """
    Local AI analyzer using Ollama for script categorization and analysis
    """
    
    def __init__(self, model: str = "llama3.2"):
        """
        Initialize Ollama analyzer
        
        Args:
            model: Ollama model to use (llama3.2, codellama, mistral, etc.)
        """
        self.model = model
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is installed and available"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _extract_script_info(self, script_content: str) -> Dict:
        """
        Extract key information from script content for better AI analysis
        
        Args:
            script_content: The full script content
            
        Returns:
            Dict with extracted information
        """
        import re
        
        info = {
            'description': '',
            'commands': [],
            'packages': [],
            'file_operations': False,
            'network_operations': False
        }
        
        # Extract comments (especially at the beginning)
        comment_lines = []
        for line in script_content.split('\n')[:50]:  # First 50 lines
            line = line.strip()
            if line.startswith('#') and not line.startswith('#!'):
                comment = line.lstrip('#').strip()
                if comment and len(comment) > 5:  # Ignore short comments
                    comment_lines.append(comment)
        
        if comment_lines:
            info['description'] = ' '.join(comment_lines[:5])  # First 5 meaningful comments
        
        # Identify key commands and operations
        install_cmds = ['apt install', 'apt-get install', 'yum install', 'dnf install', 
                       'pacman -S', 'brew install', 'pip install', 'npm install',
                       'docker pull', 'snap install', 'flatpak install']
        
        uninstall_cmds = ['apt remove', 'apt purge', 'apt-get remove', 'yum remove',
                         'dnf remove', 'pacman -R', 'brew uninstall', 'pip uninstall',
                         'npm uninstall', 'docker rmi', 'snap remove']
        
        network_cmds = ['wget', 'curl', 'git clone', 'rsync', 'scp', 'sftp', 'ftp']
        
        file_cmds = ['unrar', 'unzip', 'tar', '7z', 'convert', 'ffmpeg', 'cp', 'mv', 'rsync']
        
        # Check for these patterns
        for install_cmd in install_cmds:
            if install_cmd in script_content:
                info['commands'].append(install_cmd)
                # Extract package names after install command
                pattern = re.escape(install_cmd) + r'\s+([\w\-\.]+(?:\s+[\w\-\.]+)*)'
                matches = re.findall(pattern, script_content)
                for match in matches:
                    pkgs = match.split()
                    info['packages'].extend(pkgs[:5])  # Limit packages
        
        for uninstall_cmd in uninstall_cmds:
            if uninstall_cmd in script_content:
                info['commands'].append(uninstall_cmd)
        
        for net_cmd in network_cmds:
            if net_cmd in script_content:
                info['commands'].append(net_cmd)
                info['network_operations'] = True
        
        for file_cmd in file_cmds:
            if file_cmd in script_content:
                info['commands'].append(file_cmd)
                info['file_operations'] = True
        
        # Deduplicate commands
        info['commands'] = list(dict.fromkeys(info['commands']))
        info['packages'] = list(dict.fromkeys(info['packages']))[:10]  # Limit to 10 packages
        
        return info
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call Ollama with a prompt
        
        Args:
            prompt: The prompt to send to Ollama
            
        Returns:
            Response text or None if failed
        """
        if not self.ollama_available:
            return None
        
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model, prompt],
                capture_output=True,
                text=True,
                timeout=120  # Increased to 120 seconds for complex analysis
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Ollama error (code {result.returncode}): {result.stderr}")
                return None
            
        except subprocess.TimeoutExpired:
            print("Ollama timeout: analysis took longer than 120 seconds")
            return None
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None
    
    def analyze_script(self, script_path: str) -> Optional[Dict]:
        """
        Analyze a bash script and determine its category and properties
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Dict with analysis results or None if failed
        """
        if not self.ollama_available:
            return {
                'error': 'Ollama not available',
                'category': 'tools',
                'description': 'No AI analysis available'
            }
        
        # Read script content
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()
        except Exception as e:
            return {'error': f'Could not read script: {e}'}
        
        # Extract key information for better analysis
        script_info = self._extract_script_info(script_content)
        
        # Limit content length to avoid token limits but keep key parts
        if len(script_content) > 3000:
            # Keep beginning (shebang, comments, initial setup)
            beginning = script_content[:1500]
            # Keep end (cleanup, main logic)
            ending = script_content[-1000:]
            script_excerpt = f"{beginning}\n\n... (middle section omitted) ...\n\n{ending}"
        else:
            script_excerpt = script_content
        
        # Create enhanced analysis prompt with extracted information
        prompt = f"""Analyze this bash script and respond with ONLY valid JSON (no markdown, no code blocks, no explanations).

Script Information:
- Key Commands: {', '.join(script_info['commands'][:10])} {' (and more)' if len(script_info['commands']) > 10 else ''}
- Comments/Purpose: {script_info['description']}
- Package Operations: {', '.join(script_info['packages']) if script_info['packages'] else 'None detected'}
- File Operations: {'Yes' if script_info['file_operations'] else 'No'}
- Network Operations: {'Yes' if script_info['network_operations'] else 'No'}

Script content:
```bash
{script_excerpt}
```

Based on the script's ACTUAL behavior and commands used, categorize it:

- install: Scripts that install software (apt install, yum install, wget/curl to download installers, docker pull, pip install, npm install, etc.)
- uninstall: Scripts that remove software (apt remove, apt purge, rm -rf installations, docker rmi, cleanup operations)
- tools: Utility scripts (file conversion, backup, extraction, system maintenance, automation)
- exercises: Learning/practice scripts (tutorials, examples, tests)

Respond with this exact JSON structure:
{{
  "category": "install",
  "description": "Brief description based on what the script actually does",
  "purpose": "install_software",
  "dependencies": ["apt", "wget", "curl"],
  "safety": "safe"
}}

Purpose options: install_software, system_tool, learning, cleanup, utility, network_tool
Safety: safe (no dangerous operations), caution (modifies system), requires_review (root access, deletes files)

JSON only:"""
        
        # Get AI response
        response = self._call_ollama(prompt)
        
        if not response:
            return {
                'error': 'No response from Ollama',
                'category': 'tools',
                'description': 'AI analysis failed'
            }
        
        # Parse JSON response
        try:
            # Try to extract JSON from response (in case of extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                
                # Try to fix common JSON issues
                # Remove any trailing commas before closing braces/brackets
                json_text = json_text.replace(',]', ']').replace(',}', '}')
                # Remove multiple commas
                while ',,' in json_text:
                    json_text = json_text.replace(',,', ',')
                
                try:
                    analysis = json.loads(json_text)
                    return analysis
                except json.JSONDecodeError:
                    # If JSON parsing still fails, try to manually extract key fields
                    return self._extract_fields_from_text(response)
            else:
                # No JSON found, try parsing entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            # Try manual extraction as fallback
            result = self._extract_fields_from_text(response)
            if result:
                return result
            
            return {
                'error': f'Could not parse AI response: {e}',
                'category': 'tools',
                'description': 'AI analysis format error',
                'raw_response': response[:200]
            }
    
    def _extract_fields_from_text(self, text: str) -> Optional[Dict]:
        """
        Manually extract fields from AI response when JSON parsing fails
        
        Args:
            text: Raw response text
            
        Returns:
            Dict with extracted fields or None
        """
        import re
        
        result = {
            'category': 'tools',
            'description': 'Analysis completed',
            'dependencies': [],
            'safety': 'unknown'
        }
        
        try:
            # Extract category
            cat_match = re.search(r'"category"\s*:\s*"([^"]+)"', text)
            if cat_match:
                result['category'] = cat_match.group(1)
            
            # Extract description
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', text)
            if desc_match:
                result['description'] = desc_match.group(1)
            
            # Extract safety
            safety_match = re.search(r'"safety"\s*:\s*"([^"]+)"', text)
            if safety_match:
                result['safety'] = safety_match.group(1)
            
            # Extract dependencies
            deps_match = re.search(r'"dependencies"\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if deps_match:
                deps_str = deps_match.group(1)
                deps = re.findall(r'"([^"]+)"', deps_str)
                result['dependencies'] = deps
            
            return result
        except Exception:
            return None
    
    def batch_analyze_scripts(self, script_paths: List[str], progress_callback=None) -> Dict[str, Dict]:
        """
        Analyze multiple scripts
        
        Args:
            script_paths: List of script paths to analyze
            progress_callback: Optional callback(current, total, script_name)
            
        Returns:
            Dict mapping script_path -> analysis_result
        """
        results = {}
        total = len(script_paths)
        
        for i, script_path in enumerate(script_paths):
            if progress_callback:
                script_name = Path(script_path).name
                progress_callback(i + 1, total, script_name)
            
            results[script_path] = self.analyze_script(script_path)
        
        return results
    
    def suggest_category(self, script_name: str, script_content: str = None) -> str:
        """
        Quick category suggestion based on script name and optional content
        
        Args:
            script_name: Name of the script
            script_content: Optional script content (first few lines)
            
        Returns:
            Suggested category
        """
        # Quick heuristic-based categorization
        name_lower = script_name.lower()
        
        # Install patterns
        if any(word in name_lower for word in ['install', 'setup', 'deploy']):
            return 'install'
        
        # Uninstall patterns
        if any(word in name_lower for word in ['uninstall', 'remove', 'clean', 'purge']):
            return 'uninstall'
        
        # Exercise patterns
        if any(word in name_lower for word in ['exercise', 'test', 'practice', 'example']):
            return 'exercises'
        
        # Tools patterns
        if any(word in name_lower for word in ['tool', 'util', 'convert', 'extract', 'backup']):
            return 'tools'
        
        # If AI available, do full analysis
        if self.ollama_available and script_content:
            # For quick suggestions, use a shorter analysis
            return 'tools'  # Default fallback
        
        return 'custom'


# Convenience function
def check_ollama_available() -> bool:
    """Check if Ollama is available on the system"""
    analyzer = OllamaAnalyzer()
    return analyzer.ollama_available
