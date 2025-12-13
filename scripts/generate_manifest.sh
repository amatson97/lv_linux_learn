#!/bin/bash
# Generate manifest.json from current scripts
# This script scans all script directories and creates a comprehensive manifest

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_FILE="$REPO_ROOT/manifest.json"
REPO_VERSION=$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo "2.0.0")

# Colors
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
  echo -e "${GREEN}[*]${NC} $*"
}

warn() {
  echo -e "${YELLOW}[!]${NC} $*"
}

# Extract description from script file
get_description() {
  local script="$1"
  local desc=""
  
  # Try multiple comment patterns
  desc=$(grep -m1 '^# Description:' "$script" 2>/dev/null | sed 's/^# Description: //' || echo "")
  
  if [ -z "$desc" ]; then
    desc=$(grep -m1 '^# ' "$script" | head -1 | sed 's/^# //' || echo "")
  fi
  
  if [ -z "$desc" ]; then
    desc="Script: $(basename "$script" .sh)"
  fi
  
  # Escape quotes for JSON
  echo "$desc" | sed 's/"/\\"/g'
}

# Check if script requires sudo
requires_sudo() {
  local script="$1"
  
  if grep -q 'sudo\|apt\|systemctl' "$script" 2>/dev/null; then
    echo "true"
  else
    echo "false"
  fi
}

# Get version from script or default
get_script_version() {
  local script="$1"
  local version=""
  
  version=$(grep -m1 '^# Version:' "$script" 2>/dev/null | sed 's/^# Version: //' || echo "")
  
  if [ -z "$version" ]; then
    version="1.0.0"
  fi
  
  echo "$version"
}

generate_manifest() {
  log "Generating manifest.json..."
  
  # Start JSON
  cat > "$MANIFEST_FILE" << EOF
{
  "version": "1.0.0",
  "repository_version": "$REPO_VERSION",
  "last_updated": "$(date -Iseconds)",
  "min_app_version": "2.0.0",
  "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
  "scripts": [
EOF

  local first=true
  local script_count=0
  
  # Define categories with directory mappings
  declare -A categories=(
    ["scripts"]="install"
    ["tools"]="tools"
    ["bash_exercises"]="exercises"
    ["uninstallers"]="uninstall"
  )
  
  # Process each directory
  for dir in scripts tools bash_exercises uninstallers; do
    if [ ! -d "$REPO_ROOT/$dir" ]; then
      warn "Directory not found: $dir"
      continue
    fi
    
    category="${categories[$dir]}"
    log "Processing $dir/ ($category)..."
    
    # Find all .sh files
    while IFS= read -r script; do
      [ -f "$script" ] || continue
      
      local filename=$(basename "$script")
      
      # Skip menu utility scripts (not actual uninstallers)
      if [ "$filename" = "uninstall_menu.sh" ]; then
        continue
      fi
      
      local relative_path="${script#$REPO_ROOT/}"
      local checksum=$(sha256sum "$script" | awk '{print $1}')
      local script_id=$(echo "$filename" | sed 's/\.sh$//' | tr '_' '-')
      local script_name=$(echo "$filename" | sed 's/_/ /g' | sed 's/.sh$//' | sed 's/\b\(.\)/\u\1/g')
      local description=$(get_description "$script")
      local sudo=$(requires_sudo "$script")
      local version=$(get_script_version "$script")
      
      # Comma separator
      if [ "$first" = false ]; then
        echo "," >> "$MANIFEST_FILE"
      fi
      first=false
      
      # Generate entry
      cat >> "$MANIFEST_FILE" << ENTRY
    {
      "id": "$script_id",
      "name": "$script_name",
      "category": "$category",
      "version": "$version",
      "file_name": "$filename",
      "relative_path": "$relative_path",
      "download_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/$relative_path",
      "checksum": "sha256:$checksum",
      "description": "$description",
      "requires_sudo": $sudo,
      "dependencies": [],
      "tags": [],
      "last_modified": "$(date -Iseconds)"
    }
ENTRY
      
      script_count=$((script_count + 1))
    done < <(find "$REPO_ROOT/$dir" -maxdepth 1 -name "*.sh" -type f 2>/dev/null | sort)
  done
  
  # Close JSON
  cat >> "$MANIFEST_FILE" << 'EOF'
  ]
}
EOF

  log "Generated manifest with $script_count scripts"
  log "Manifest saved to: $MANIFEST_FILE"
}

# Main execution
log "Starting manifest generation..."
log "Repository root: $REPO_ROOT"
log "Repository version: $REPO_VERSION"

generate_manifest

log "Done!"
