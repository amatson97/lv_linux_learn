#!/bin/bash
# Interactive menu for lv_linux_learn scripts
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$script_dir/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$script_dir/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

# Repository system
if [ -f "$script_dir/includes/repository.sh" ]; then
  # shellcheck source=/dev/null
  source "$script_dir/includes/repository.sh"
fi

# Custom scripts configuration (DEPRECATED - use Custom Manifests instead)
# Custom scripts functionality removed to match menu.py design
# Scripts are now managed through manifest system only
CUSTOM_SCRIPTS_DIR="$HOME/.lv_linux_learn"
CUSTOM_SCRIPTS_JSON="$CUSTOM_SCRIPTS_DIR/custom_scripts.json"
MANIFEST_CACHE="$CUSTOM_SCRIPTS_DIR/manifest.json"

# Manifest URL (can be overridden by config)
DEFAULT_MANIFEST_URL="https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
MANIFEST_URL="${CUSTOM_MANIFEST_URL:-$DEFAULT_MANIFEST_URL}"

# Store original URL for reference
ORIGINAL_MANIFEST_URL="$MANIFEST_URL"

# Repository system variables
REPO_ENABLED=false
REPO_UPDATES_AVAILABLE=0

# Search filter
SEARCH_FILTER=""

# Dynamic category mapping (initialized in show_main_menu)
DYNAMIC_CATEGORY_MAP=""

# Dynamic arrays loaded from manifest
declare -a SCRIPTS=()
declare -a DESCRIPTIONS=()
declare -a MENU_SCRIPT_IDS=()

# Ensure cache directory exists
mkdir -p "$CUSTOM_SCRIPTS_DIR"

# Download manifest from configured URL if not cached or older than 1 hour
fetch_manifest() {
  local cache_age=0
  
  # Priority System (from highest to lowest):
  # 1. Environment variable CUSTOM_MANIFEST_URL (for testing/override)
  # 2. Custom manifest URL (custom_manifest_url in config)
  # 3. Public repository (if use_public_repository=true and no custom manifest)
  # 4. Error (if both disabled)
  #
  # NOTE: The use_public_repository toggle NEVER affects custom manifests.
  # Custom manifests are managed exclusively via the Custom Manifests menu.
  
  # Check environment variable first (highest priority for testing)
  local force_download=false
  if [ -n "${CUSTOM_MANIFEST_URL:-}" ]; then
    MANIFEST_URL="$CUSTOM_MANIFEST_URL"
    green_echo "[*] Using custom manifest from environment variable"
    # Force fresh download when environment variable is set (bypass cache)
    force_download=true
  else
    # Check for custom manifest URL in config (second priority)
    local custom_manifest_url
    custom_manifest_url=$(get_config_value "custom_manifest_url" "")
    
    if [ -n "$custom_manifest_url" ]; then
      # Custom manifest configured - use it regardless of public repo setting
      MANIFEST_URL="$custom_manifest_url"
      green_echo "[*] Using custom manifest (takes priority over public repository)"
    else
      # No custom manifest - check if public repository is enabled
      local use_public_repo
      use_public_repo=$(get_config_value "use_public_repository" "true")
      
      if [ "$use_public_repo" != "true" ]; then
        # Public repository disabled and no custom manifest
        green_echo "[!] Public repository disabled and no custom manifest configured"
        green_echo "[*] Configure a custom manifest in the 'Custom Manifests' menu"
        return 1
      fi
      
      # Public repo enabled and no custom manifest - use default repository
      MANIFEST_URL="${DEFAULT_MANIFEST_URL}"
    fi
  fi
  
  if [ -f "$MANIFEST_CACHE" ]; then
    cache_age=$(( $(date +%s) - $(stat -c %Y "$MANIFEST_CACHE" 2>/dev/null || echo 0) ))
  fi
  
  # Fetch if cache doesn't exist, is older than 1 hour, or force_download is true
  if [ ! -f "$MANIFEST_CACHE" ] || [ $cache_age -gt 3600 ] || [ "$force_download" = true ]; then
    green_echo "[*] Fetching latest manifest..."
    green_echo "[*] Connecting to: $MANIFEST_URL"
    
    local download_success=false
    if command -v curl &> /dev/null; then
      green_echo "[*] Using curl for download..."
      if curl -sS -f -o "$MANIFEST_CACHE" "$MANIFEST_URL"; then
        download_success=true
      else
        green_echo "[!] Failed to fetch manifest with curl"
      fi
    elif command -v wget &> /dev/null; then
      green_echo "[*] Using wget for download..."
      if wget -q -O "$MANIFEST_CACHE" "$MANIFEST_URL"; then
        download_success=true
      else
        green_echo "[!] Failed to fetch manifest with wget"
      fi
    else
      green_echo "[!] Error: Neither curl nor wget is installed"
      return 1
    fi
    
    if [ "$download_success" = true ]; then
      local file_size
      file_size=$(stat -c%s "$MANIFEST_CACHE" 2>/dev/null || echo "unknown")
      green_echo "[*] Downloaded ${file_size} bytes"
      green_echo "[*] Cached to: $MANIFEST_CACHE"
      green_echo "[+] Manifest updated successfully"
    else
      return 1
    fi
  fi
  
  return 0
}

# Load scripts from manifest.json
load_scripts_from_manifest() {
  # Fetch latest manifest
  fetch_manifest || {
    green_echo "[!] Warning: Could not fetch manifest. Using cached version if available."
  }
  
  local manifest_path="$MANIFEST_CACHE"
  
  if [ ! -f "$manifest_path" ]; then
    green_echo "[!] Error: No manifest file available (cached or downloaded)"
    green_echo "[!] Please check your internet connection and try again"
    return 1
  fi
  
  # Check if jq is available
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Warning: 'jq' not installed. Cannot load scripts from manifest."
    return 1
  fi
  
  # Display manifest information
  local manifest_version repo_version last_updated total_scripts
  manifest_version=$(jq -r '.version // "unknown"' "$manifest_path" 2>/dev/null)
  repo_version=$(jq -r '.repository_version // .manifest_version // "unknown"' "$manifest_path" 2>/dev/null)
  last_updated=$(jq -r '.last_updated // .created // "unknown"' "$manifest_path" 2>/dev/null)
  
  # Check if this is a nested (custom) or flat (public) manifest
  local is_nested
  is_nested=$(jq -r '.scripts | type' "$manifest_path" 2>/dev/null)
  
  if [ "$is_nested" = "object" ]; then
    # Custom manifest - nested by category
    total_scripts=$(jq '.total_scripts // 0' "$manifest_path" 2>/dev/null)
  else
    # Public manifest - flat array
    total_scripts=$(jq '.scripts | length' "$manifest_path" 2>/dev/null || echo 0)
  fi
  
  green_echo "[*] Loaded manifest version $manifest_version (repo: $repo_version)"
  green_echo "[*] Last updated: $last_updated"
  green_echo "[*] Processing $total_scripts scripts..."
  
  # Clear arrays
  SCRIPTS=()
  DESCRIPTIONS=()
  MENU_SCRIPT_IDS=()
  
  # Track scripts per category
  local install_count=0 tools_count=0 exercises_count=0 uninstall_count=0
  declare -A dynamic_category_counts
  
  # Get all categories from manifest (supports dynamic categories)
  local all_categories
  if [ "$is_nested" = "object" ]; then
    # Custom manifest - get categories from object keys
    all_categories=$(jq -r '.scripts | keys[]' "$manifest_path" 2>/dev/null)
  else
    # Public manifest - get unique categories from scripts
    all_categories=$(jq -r '.scripts[].category' "$manifest_path" 2>/dev/null | sort -u)
  fi
  
  # Standard categories to process first
  local standard_categories=("install" "tools" "exercises" "uninstall")
  
  # Process standard categories first, then dynamic categories
  for category in "${standard_categories[@]}"; do
    if echo "$all_categories" | grep -q "^${category}$"; then
      local category_scripts count=0
      
      if [ "$is_nested" = "object" ]; then
        # Custom manifest - get scripts from nested structure
        category_scripts=$(jq -r ".scripts.${category}[]?.relative_path // .scripts.${category}[]?.download_url" "$manifest_path" 2>/dev/null | sed 's|^file://||')
      else
        # Public manifest - filter by category
        category_scripts=$(jq -r ".scripts[] | select(.category == \"$category\") | .relative_path" "$manifest_path" 2>/dev/null)
      fi
      
      if [ -n "$category_scripts" ]; then
        # Add scripts from this category
        while IFS= read -r script_path; do
          [ -z "$script_path" ] && continue
          SCRIPTS+=("$script_path")
          
          # Get description and ID for this script
          local desc script_id
          if [ "$is_nested" = "object" ]; then
            desc=$(jq -r ".scripts.${category}[]? | select(.relative_path == \"$script_path\" or .download_url | endswith(\"$script_path\")) | .description" "$manifest_path" 2>/dev/null)
            script_id=$(jq -r ".scripts.${category}[]? | select(.relative_path == \"$script_path\" or .download_url | endswith(\"$script_path\")) | .id" "$manifest_path" 2>/dev/null)
          else
            desc=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .description" "$manifest_path" 2>/dev/null)
            script_id=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .id" "$manifest_path" 2>/dev/null)
          fi
          
          DESCRIPTIONS+=("$desc")
          MENU_SCRIPT_IDS+=("$script_id")
          count=$((count + 1))
        done <<< "$category_scripts"
        
        # Update category counter
        case "$category" in
          install) install_count=$count ;;
          tools) tools_count=$count ;;
          exercises) exercises_count=$count ;;
          uninstall) uninstall_count=$count ;;
        esac
        
        # Add separator after each category (except last)
        if [ "$category" != "uninstall" ]; then
          SCRIPTS+=("")
          MENU_SCRIPT_IDS+=("__separator__")
          local separator_name
          case "$category" in
            install) separator_name="Utility Tools" ;;
            tools) separator_name="Bash Exercises" ;;
            exercises) separator_name="Uninstall" ;;
          esac
          DESCRIPTIONS+=("── $separator_name ──")
        fi
      fi
    fi
  done
  
  # Now process any non-standard (dynamic) categories
  while IFS= read -r category; do
    # Skip if it's a standard category
    if [[ " ${standard_categories[*]} " =~ " ${category} " ]]; then
      continue
    fi
    
    local category_scripts count=0
    
    if [ "$is_nested" = "object" ]; then
      # Custom manifest - get scripts from nested structure
      category_scripts=$(jq -r ".scripts.${category}[]?.relative_path // .scripts.${category}[]?.download_url" "$manifest_path" 2>/dev/null | sed 's|^file://||')
    else
      # Public manifest - filter by category
      category_scripts=$(jq -r ".scripts[] | select(.category == \"$category\") | .relative_path" "$manifest_path" 2>/dev/null)
    fi
    
    if [ -n "$category_scripts" ]; then
      # Add separator for this dynamic category
      SCRIPTS+=("")
      MENU_SCRIPT_IDS+=("__separator__")
      DESCRIPTIONS+=("── ${category^} ──")
      
      # Add scripts from this category
      while IFS= read -r script_path; do
        [ -z "$script_path" ] && continue
        SCRIPTS+=("$script_path")
        
        # Get description and ID for this script
        local desc script_id
        if [ "$is_nested" = "object" ]; then
          # For custom manifests, match by relative_path OR download_url
          desc=$(jq -r ".scripts.${category}[]? | select(.relative_path == \"$script_path\" or (.download_url // \"\" | endswith(\"$script_path\"))) | .description" "$manifest_path" 2>/dev/null)
          script_id=$(jq -r ".scripts.${category}[]? | select(.relative_path == \"$script_path\" or (.download_url // \"\" | endswith(\"$script_path\"))) | .id" "$manifest_path" 2>/dev/null)
        else
          desc=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .description" "$manifest_path" 2>/dev/null)
          script_id=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .id" "$manifest_path" 2>/dev/null)
        fi
        
        DESCRIPTIONS+=("$desc")
        MENU_SCRIPT_IDS+=("$script_id")
        count=$((count + 1))
      done <<< "$category_scripts"
      
      # Track dynamic category count
      dynamic_category_counts[$category]=$count
    fi
  done <<< "$all_categories"
  
  # Display category breakdown
  green_echo "[*] Script breakdown:"
  [ $install_count -gt 0 ] && green_echo "    Install: $install_count scripts"
  [ $tools_count -gt 0 ] && green_echo "    Tools: $tools_count scripts"
  [ $exercises_count -gt 0 ] && green_echo "    Exercises: $exercises_count scripts"
  [ $uninstall_count -gt 0 ] && green_echo "    Uninstall: $uninstall_count scripts"
  
  # Display dynamic categories
  for category in "${!dynamic_category_counts[@]}"; do
    green_echo "    ${category^}: ${dynamic_category_counts[$category]} scripts"
  done
  
  return 0
}

# DEPRECATED: Custom scripts functions - no longer used
# Custom scripts now managed through Custom Manifests system only
# These functions are kept for backward compatibility but not called

# Load custom scripts from JSON and append to arrays
load_custom_scripts() {
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    return 0
  fi
  
  # Check if jq is available
  if ! command -v jq &> /dev/null; then
    return 0
  fi
  
  # Simply append custom scripts at the end for now (simpler, always works)
  local custom_count
  custom_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON" 2>/dev/null || echo "0")
  
  if [ "$custom_count" -gt 0 ]; then
    # Add separator before custom scripts
    SCRIPTS+=("")
    DESCRIPTIONS+=("── Custom Scripts ──")
    
    # Add all custom scripts
    local i
    for ((i=0; i<custom_count; i++)); do
      local script_path name desc
      script_path=$(jq -r ".scripts[$i].script_path" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null)
      name=$(jq -r ".scripts[$i].name" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null)
      desc=$(jq -r ".scripts[$i].description" "$CUSTOM_SCRIPTS_JSON" 2>/dev/null | sed 's/<[^>]*>//g')
      
      if [ -n "$script_path" ]; then
        SCRIPTS+=("$script_path")
        DESCRIPTIONS+=("📝 $desc")
      fi
    done
  fi
}

# Reload custom scripts (removes old custom scripts and reloads from JSON)
reload_custom_scripts() {
  # Reload entire script list from manifest
  load_scripts_from_manifest
  
  # Then append custom scripts
  load_custom_scripts
}

# Function to refresh script counts for main menu
refresh_script_counts() {
  if [ -f "$MANIFEST_CACHE" ] && command -v jq &> /dev/null; then
    CACHED_INSTALL_COUNT=$(jq -r '[.scripts[] | select(.category == "install")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
    CACHED_TOOLS_COUNT=$(jq -r '[.scripts[] | select(.category == "tools")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
    CACHED_EXERCISES_COUNT=$(jq -r '[.scripts[] | select(.category == "exercises")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
    CACHED_UNINSTALL_COUNT=$(jq -r '[.scripts[] | select(.category == "uninstall")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
  fi
}

# Initialize: Update manifest URL if custom URL is set
if [ -n "${CUSTOM_MANIFEST_URL:-}" ]; then
  MANIFEST_URL="$CUSTOM_MANIFEST_URL"
  # Clear cached manifest to force download from new URL
  rm -f "$MANIFEST_CACHE" 2>/dev/null || true
fi

# Initialize: load scripts from manifest
load_scripts_from_manifest

# DEPRECATED: Custom scripts no longer loaded separately
# Scripts are now managed through manifest system only (Custom Manifests tab)
# load_custom_scripts  # Commented out to match menu.py design

# Cache the script counts for main menu display
refresh_script_counts

# ============================================================================
# Path Resolution for Cached Scripts
# ============================================================================

ensure_remote_includes() {
  local cache_root="$1"
  local includes_cache="$cache_root/includes"
  
  # Get repository URL from manifest
  local repo_url=""
  if [ -f "$MANIFEST_CACHE" ] && command -v jq &> /dev/null; then
    repo_url=$(jq -r '.repository_url // ""' "$MANIFEST_CACHE" 2>/dev/null)
  fi
  
  if [ -z "$repo_url" ]; then
    echo "[INFO] No repository URL found in manifest, using local includes" >&2
    return 1
  fi
  
  # Check if we already have remote includes cached
  if [ -d "$includes_cache" ] && [ ! -L "$includes_cache" ]; then
    # Check if cached includes are from remote repository
    local cached_origin=""
    if [ -f "$includes_cache/.origin" ]; then
      cached_origin=$(cat "$includes_cache/.origin" 2>/dev/null || echo "")
    fi
    
    if [ "$cached_origin" = "$repo_url" ]; then
      # Check freshness (within 24 hours)
      local cache_time=0
      if [ -f "$includes_cache/.timestamp" ]; then
        cache_time=$(cat "$includes_cache/.timestamp" 2>/dev/null || echo 0)
      fi
      local current_time=$(date +%s)
      local age=$((current_time - cache_time))
      
      if [ $age -lt 86400 ]; then # 24 hours
        echo "[INFO] Using cached remote includes (age: ${age}s)" >&2
        return 0
      fi
    fi
  fi
  
  # Download remote includes
  echo "[INFO] Downloading includes from remote repository: $repo_url" >&2
  
  # Remove existing includes if it exists
  if [ -e "$includes_cache" ]; then
    rm -rf "$includes_cache" 2>/dev/null || {
      echo "[WARNING] Cannot remove existing includes cache: $includes_cache" >&2
      return 1
    }
  fi
  
  # Create temporary directory for download
  local temp_dir=$(mktemp -d 2>/dev/null || echo "/tmp/includes_$$")
  trap "rm -rf '$temp_dir' 2>/dev/null || true" EXIT
  
  # Try to download main.sh and repository.sh
  local download_success=false
  
  if command -v curl &> /dev/null; then
    if curl -sS -f -o "$temp_dir/main.sh" "$repo_url/includes/main.sh" 2>/dev/null && \
       curl -sS -f -o "$temp_dir/repository.sh" "$repo_url/includes/repository.sh" 2>/dev/null; then
      download_success=true
    fi
  elif command -v wget &> /dev/null; then
    if wget -q -O "$temp_dir/main.sh" "$repo_url/includes/main.sh" 2>/dev/null && \
       wget -q -O "$temp_dir/repository.sh" "$repo_url/includes/repository.sh" 2>/dev/null; then
      download_success=true
    fi
  fi
  
  if [ "$download_success" = true ]; then
    # Create includes directory and copy files
    mkdir -p "$includes_cache"
    cp "$temp_dir"/*.sh "$includes_cache/" 2>/dev/null
    chmod +x "$includes_cache"/*.sh 2>/dev/null
    
    # Mark cache with origin and timestamp
    echo "$repo_url" > "$includes_cache/.origin"
    date +%s > "$includes_cache/.timestamp"
    
    echo "[INFO] Successfully downloaded remote includes to cache" >&2
    return 0
  else
    echo "[WARNING] Failed to download remote includes from: $repo_url" >&2
    return 1
  fi
}

# Ensure includes directory is available for cached scripts
ensure_cache_includes_symlink() {
  local cache_root="$HOME/.lv_linux_learn/script_cache"
  local includes_symlink="$cache_root/includes"
  
  # Ensure cache directory exists
  if [ ! -d "$cache_root" ]; then
    if ! mkdir -p "$cache_root" 2>/dev/null; then
      echo "[WARNING] No permission to create cache directory: $cache_root" >&2
      return 1
    fi
  fi
  
  # Try to get remote includes first, then fall back to local
  if ensure_remote_includes "$cache_root"; then
    return 0
  fi
  
  # Fall back to local repository includes
  local repo_includes="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/includes"
  if [ ! -d "$repo_includes" ]; then
    echo "[WARNING] Local repository includes directory not found: $repo_includes" >&2
    return 1
  fi
  
  # Handle existing symlink/file
  if [ -e "$includes_symlink" ] || [ -L "$includes_symlink" ]; then
    if [ -L "$includes_symlink" ]; then
      # Check if symlink points to correct location
      local current_target
      current_target=$(readlink "$includes_symlink" 2>/dev/null || echo "")
      if [ "$(realpath "$current_target" 2>/dev/null || echo "")" = "$(realpath "$repo_includes" 2>/dev/null || echo "")" ]; then
        # Symlink already correct
        return 0
      else
        # Symlink points to wrong location, remove and recreate
        if ! rm "$includes_symlink" 2>/dev/null; then
          echo "[WARNING] Cannot remove existing symlink: $includes_symlink" >&2
          return 1
        fi
        echo "[INFO] Removed outdated symlink: $includes_symlink" >&2
      fi
    else
      # Regular file/directory exists with same name
      echo "[WARNING] File/directory exists at symlink path: $includes_symlink" >&2
      return 1
    fi
  fi
  
  # Create the symlink
  if ln -s "$repo_includes" "$includes_symlink" 2>/dev/null; then
    echo "[INFO] Created includes symlink: $includes_symlink -> $repo_includes" >&2
    return 0
  else
    local errno=$?
    if [ $errno -eq 1 ]; then
      echo "[WARNING] Symlinks not supported on this filesystem" >&2
    else
      echo "[WARNING] Cannot create symlink (filesystem issue)" >&2
    fi
    return 1
  fi
}

# Fallback method: copy includes directory if symlink creation fails
fallback_copy_includes() {
  local cache_root="$HOME/.lv_linux_learn/script_cache"
  local includes_cache="$cache_root/includes"
  
  # Try remote includes first
  if ensure_remote_includes "$cache_root"; then
    return 0
  fi
  
  # Fall back to local repository includes
  local repo_includes="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/includes"
  if [ ! -d "$repo_includes" ]; then
    echo "[WARNING] Local repository includes directory not found: $repo_includes" >&2
    return 1
  fi
  
  # Remove existing includes if it exists
  if [ -e "$includes_cache" ]; then
    if ! rm -rf "$includes_cache" 2>/dev/null; then
      echo "[WARNING] Cannot remove existing includes directory: $includes_cache" >&2
      return 1
    fi
  fi
  
  # Copy the includes directory
  if cp -r "$repo_includes" "$includes_cache" 2>/dev/null; then
    echo "[INFO] Copied includes directory to cache (symlink fallback): $includes_cache" >&2
    return 0
  else
    echo "[WARNING] Cannot copy includes directory" >&2
    return 1
  fi
}

# Check if copied includes directory is up to date with repository
check_includes_freshness() {
  local cache_root="$HOME/.lv_linux_learn/script_cache"
  local includes_cache="$cache_root/includes"
  
  if [ ! -d "$includes_cache" ]; then
    return 1
  fi
  
  # If it's a symlink to local repo, check if target exists
  if [ -L "$includes_cache" ]; then
    local target=$(readlink "$includes_cache" 2>/dev/null || echo "")
    if [ -d "$target" ]; then
      return 0
    else
      # Symlink is broken
      return 1
    fi
  fi
  
  # For cached remote includes, check age and origin
  if [ -f "$includes_cache/.origin" ] && [ -f "$includes_cache/.timestamp" ]; then
    local cache_time=$(cat "$includes_cache/.timestamp" 2>/dev/null || echo 0)
    local current_time=$(date +%s)
    local age=$((current_time - cache_time))
    
    # Consider fresh if less than 24 hours old
    if [ $age -lt 86400 ]; then
      return 0
    fi
  fi
  
  # For local copied includes, compare with local repository
  local repo_includes="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/includes"
  if [ -d "$repo_includes" ]; then
    local cache_main="$includes_cache/main.sh"
    local repo_main="$repo_includes/main.sh"
    
    if [ -f "$cache_main" ] && [ -f "$repo_main" ]; then
      local cache_mtime repo_mtime
      cache_mtime=$(stat -c %Y "$cache_main" 2>/dev/null || echo 0)
      repo_mtime=$(stat -c %Y "$repo_main" 2>/dev/null || echo 0)
      
      # Consider fresh if cache is newer or equal (within 1 second tolerance)
      [ $cache_mtime -ge $((repo_mtime - 1)) ]
    else
      return 1
    fi
  else
    # No local repository to compare with, assume cached version is fresh
    return 0
  fi
}

# Ensure includes directory is available in cache (symlink preferred, copy as fallback)
ensure_includes_available() {
  # Check if we already have fresh includes
  if check_includes_freshness; then
    return 0
  fi
  
  # Try symlink first
  if ensure_cache_includes_symlink; then
    return 0
  fi
  
  # Fall back to copying if symlink fails
  echo "[INFO] Symlink failed, trying copy fallback..." >&2
  if fallback_copy_includes; then
    return 0
  fi
  
  echo "[ERROR] Both symlink and copy methods failed - cached scripts may not work properly" >&2
  return 1
}

# Initialize repository system
if type -t init_repo_config &>/dev/null; then
  init_repo_config
  REPO_ENABLED=true
  
  # Load custom manifest URL from config if set
  custom_url=$(get_config_value 'custom_manifest_url' '' 2>/dev/null || echo "")
  if [ -n "$custom_url" ]; then
    export CUSTOM_MANIFEST_URL="$custom_url"
    MANIFEST_URL="$custom_url"
  fi
  
  # Check for updates on startup if auto-check is enabled
  if [ "$(get_config_value 'auto_check_updates' 'true')" = "true" ]; then
    check_for_updates &>/dev/null || true
  fi
else
  # Enable basic repository functionality even without full repository.sh
  REPO_ENABLED=true
fi

# Repository Management Functions
# =============================================================================

download_all_scripts() {
  # Check if repository system is available
  if [ "$REPO_ENABLED" != "true" ]; then
    green_echo "[!] Repository system not enabled"
    return 1
  fi
  
  # Call the repository download function
  # This function exists in includes/repository.sh
  if command -v fetch_remote_manifest &> /dev/null; then
    # Fetch manifest first
    if [ ! -f "$MANIFEST_FILE" ]; then
      green_echo "[*] Fetching manifest..."
      if ! fetch_remote_manifest; then
        green_echo "[!] Failed to fetch manifest"
        return 1
      fi
    fi
    
    green_echo "[*] Downloading all scripts from repository..."
    
    local script_count=$(get_script_count)
    local downloaded=0
    local failed=0
    
    for ((i=0; i<script_count; i++)); do
      local script_id=$(jq -r ".scripts[$i].id" "$MANIFEST_FILE" 2>/dev/null)
      local script_name=$(jq -r ".scripts[$i].name" "$MANIFEST_FILE" 2>/dev/null)
      
      if [ "$script_id" != "null" ] && [ -n "$script_id" ]; then
        echo "[*] Downloading $script_name..."
        
        if download_script "$script_id"; then
          downloaded=$((downloaded + 1))
        else
          failed=$((failed + 1))
        fi
      fi
    done
    
    green_echo "[+] Download complete: $downloaded downloaded, $failed failed"
    
    # Refresh script arrays after download
    load_scripts_from_manifest
  else
    green_echo "[!] Repository functions not available"
    return 1
  fi
}

list_cached_scripts() {
  local cache_dir="$HOME/.lv_linux_learn/script_cache"
  
  if [ ! -d "$cache_dir" ]; then
    green_echo "[!] No script cache directory found"
    return 1
  fi
  
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                           Cached Scripts                                       ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  local total_cached=0
  local categories=("install" "tools" "exercises" "uninstall")
  
  # Check if we have manifest for enhanced info
  local has_manifest=false
  if [ -f "$MANIFEST_CACHE" ] && command -v jq &> /dev/null; then
    has_manifest=true
  fi
  
  # Print table header with better spacing
  printf "  \033[1m%-6s %-40s %-12s %-10s %-13s %-12s\033[0m\n" "Status" "Script Name" "Category" "Size" "Modified" "Source"
  printf "  %-6s %-40s %-12s %-10s %-13s %-12s\n" "──────" "────────────────────────────────────────" "────────────" "──────────" "─────────────" "────────────"
  
  for category in "${categories[@]}"; do
    local category_dir="$cache_dir/$category"
    if [ -d "$category_dir" ]; then
      # Find all cached scripts in this category
      while IFS= read -r script_file; do
        [ -z "$script_file" ] && continue
        
        local script_name=$(basename "$script_file")
        local size_bytes=$(stat -c%s "$script_file" 2>/dev/null || echo "0")
        local size_kb=$((size_bytes / 1024))
        local modified=$(stat -c%y "$script_file" 2>/dev/null | cut -d' ' -f1)
        
        # Determine source from manifest
        local source="Local"
        local script_id=""
        local status="✓"
        
        if [ "$has_manifest" = true ]; then
          # Try to find script in manifest (handle jq failures gracefully for pipefail)
          script_id=$(jq -r ".scripts[] | select(.file_name == \"$script_name\" or .relative_path | endswith(\"$script_name\")) | .id" "$MANIFEST_CACHE" 2>/dev/null | head -1 || echo "")
          
          if [ -n "$script_id" ] && [ "$script_id" != "null" ]; then
            # Check if update available by comparing checksums
            local remote_checksum=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .checksum" "$MANIFEST_CACHE" 2>/dev/null | sed 's/^sha256://' || echo "")
            local verify_checksums=$(jq -r '.verify_checksums // true' "$MANIFEST_CACHE" 2>/dev/null || echo "true")
            
            # Get source/repository info
            local repo_url=$(jq -r '.repository_url // ""' "$MANIFEST_CACHE" 2>/dev/null || echo "")
            if [ -n "$repo_url" ] && [ "$repo_url" != "null" ]; then
              if [[ "$repo_url" == *"github.com/amatson97/lv_linux_learn"* ]]; then
                source="Public"
              else
                source="Custom"
              fi
            fi
            
            # Check for updates if checksums enabled
            if [ -n "$remote_checksum" ] && [ "$remote_checksum" != "null" ] && [ "$verify_checksums" = "true" ]; then
              local local_checksum=$(sha256sum "$script_file" 2>/dev/null | cut -d' ' -f1 || echo "")
              if [ -n "$local_checksum" ] && [ "$local_checksum" != "$remote_checksum" ]; then
                status="📥"
              fi
            fi
          fi
        fi
        
        # Print row with color coding and better alignment
        if [ "$status" = "📥" ]; then
          printf "  \033[1;33m%-6s\033[0m" "$status"
        else
          printf "  \033[1;32m%-6s\033[0m" "$status"
        fi
        printf "%-40s \033[2m%-12s\033[0m \033[1m%-10s\033[0m %-13s \033[2m%-12s\033[0m\n" "$script_name" "$category" "${size_kb}KB" "$modified" "$source"
        
        total_cached=$((total_cached + 1))
      done < <(find "$category_dir" -name "*.sh" 2>/dev/null | sort)
    fi
  done
  
  echo
  if [ "$total_cached" -eq 0 ]; then
    echo "  No scripts currently cached."
    echo "  Use 'Download All Scripts' option to populate the cache."
  else
    echo "  \033[1mTotal cached scripts: $total_cached\033[0m"
    echo
    echo "  Legend: ✓ = Cached & Up-to-date  |  📥 = Update Available  |  ☁️ = Not Cached"
  fi
  echo
}

clear_script_cache() {
  local cache_dir="$HOME/.lv_linux_learn/script_cache"
  
  if [ ! -d "$cache_dir" ]; then
    green_echo "[!] No script cache directory found"
    return 0
  fi
  
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Clear Script Cache                                     ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Count cached scripts
  local total_cached=0
  for category in install tools exercises uninstall; do
    if [ -d "$cache_dir/$category" ]; then
      local count=$(find "$cache_dir/$category" -name "*.sh" | wc -l)
      total_cached=$((total_cached + count))
    fi
  done
  
  if [ "$total_cached" -eq 0 ]; then
    green_echo "[!] Cache is already empty"
    return 0
  fi
  
  echo "  This will remove all $total_cached cached scripts."
  echo "  You can download them again later using the repository options."
  echo
  read -rp "  Continue? [y/N]: " confirm
  
  if [[ "${confirm,,}" != "y" ]]; then
    green_echo "[*] Cache clear cancelled"
    return 0
  fi
  
  # Remove cached scripts but preserve directory structure
  for category in install tools exercises uninstall; do
    if [ -d "$cache_dir/$category" ]; then
      rm -f "$cache_dir/$category"/*.sh 2>/dev/null || true
    fi
  done
  
  # Remove includes symlink/directory if it exists
  if [ -L "$cache_dir/includes" ]; then
    rm -f "$cache_dir/includes"
  elif [ -d "$cache_dir/includes" ]; then
    rm -rf "$cache_dir/includes"
  fi
  
  green_echo "[+] Script cache cleared successfully"
  
  # Refresh script arrays after clearing cache
  load_scripts_from_manifest
}

download_single_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                      Download Individual Script                                ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  if [ ! -f "$MANIFEST_CACHE" ]; then
    green_echo "[!] No manifest found"
    return 1
  fi
  
  # Get total scripts
  local total_scripts=$(jq -r '.scripts | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
  
  if [ "$total_scripts" -eq 0 ]; then
    green_echo "[!] No scripts available in repository"
    return 1
  fi
  
  # Group scripts by category for display
  declare -A category_scripts
  local categories=("install" "tools" "exercises" "uninstall")
  
  # Load all scripts grouped by category
  for category in "${categories[@]}"; do
    local scripts=$(jq -r ".scripts[] | select(.category == \"$category\") | .id + \"|\" + .file_name + \"|\" + (.description // \"No description\")" "$MANIFEST_CACHE" 2>/dev/null || echo "")
    if [ -n "$scripts" ]; then
      category_scripts["$category"]="$scripts"
    fi
  done
  
  # Display by category
  echo "  Filter by category:"
  echo "   1) 📦 Install Scripts"
  echo "   2) 🔧 Tools & Utilities"
  echo "   3) 📚 Bash Exercises"
  echo "   4) ⚠️  Uninstall Scripts"
  echo "   a) Show All Scripts"
  echo
  read -rp "Select category (1-4, a, or 0 to cancel): " cat_choice
  
  local selected_category=""
  case "$cat_choice" in
    1) selected_category="install" ;;
    2) selected_category="tools" ;;
    3) selected_category="exercises" ;;
    4) selected_category="uninstall" ;;
    a|A) selected_category="all" ;;
    0) return 0 ;;
    *)
      green_echo "[!] Invalid choice"
      sleep 1
      return 1
      ;;
  esac
  
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                      Available Scripts to Download                             ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Build list of scripts to display
  declare -a script_ids
  declare -a script_names
  declare -a script_descs
  declare -a script_cats
  local count=0
  
  if [ "$selected_category" = "all" ]; then
    # Show all scripts
    for category in "${categories[@]}"; do
      if [ -n "${category_scripts[$category]}" ]; then
        while IFS='|' read -r id name desc; do
          count=$((count + 1))
          script_ids+=("$id")
          script_names+=("$name")
          script_descs+=("$desc")
          script_cats+=("$category")
        done <<< "${category_scripts[$category]}"
      fi
    done
  else
    # Show scripts from selected category
    if [ -n "${category_scripts[$selected_category]}" ]; then
      while IFS='|' read -r id name desc; do
        count=$((count + 1))
        script_ids+=("$id")
        script_names+=("$name")
        script_descs+=("$desc")
        script_cats+=("$selected_category")
      done <<< "${category_scripts[$selected_category]}"
    fi
  fi
  
  if [ "$count" -eq 0 ]; then
    green_echo "[!] No scripts found"
    return 1
  fi
  
  # Display scripts with status indicators
  for i in $(seq 0 $((count - 1))); do
    local script_id="${script_ids[$i]}"
    local script_name="${script_names[$i]}"
    local desc="${script_descs[$i]}"
    local cat="${script_cats[$i]}"
    local num=$((i + 1))
    
    # Check if already cached
    local status="☁️"
    local status_text="Not Cached"
    if type get_cached_script_path &> /dev/null; then
      local cached_path=$(get_cached_script_path "$script_id" 2>/dev/null || echo "")
      if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
        status="✓"
        status_text="Cached"
      fi
    fi
    
    printf "  %2d) \033[1m%-35s\033[0m [%s \033[2m%s\033[0m]\n" "$num" "$script_name" "$status" "$status_text"
    printf "      \033[2m%s\033[0m\n" "$desc"
  done
  
  echo
  echo "  ────────────────────────────────────────────────────────────────────────────"
  echo
  read -rp "Select script to download (1-$count, or 0 to cancel): " script_choice
  
  if [ "$script_choice" = "0" ] || [ -z "$script_choice" ]; then
    return 0
  fi
  
  if [[ ! "$script_choice" =~ ^[0-9]+$ ]] || [ "$script_choice" -lt 1 ] || [ "$script_choice" -gt "$count" ]; then
    green_echo "[!] Invalid choice"
    sleep 1
    return 1
  fi
  
  local idx=$((script_choice - 1))
  local selected_id="${script_ids[$idx]}"
  local selected_name="${script_names[$idx]}"
  
  # Check if already cached
  if type get_cached_script_path &> /dev/null; then
    local cached_path=$(get_cached_script_path "$selected_id" 2>/dev/null || echo "")
    if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
      echo
      green_echo "[!] $selected_name is already cached"
      read -rp "Download again (overwrite)? [y/N]: " overwrite
      if [[ "${overwrite,,}" != "y" ]]; then
        green_echo "[*] Download cancelled"
        return 0
      fi
    fi
  fi
  
  echo
  green_echo "[*] Downloading $selected_name..."
  
  if download_script "$selected_id"; then
    green_echo "[+] Successfully downloaded $selected_name to cache!"
  else
    green_echo "[!] Failed to download $selected_name"
    return 1
  fi
}

remove_cached_script() {
  local script_name="$1"
  local cache_dir="$HOME/.lv_linux_learn/script_cache"
  
  if [ -z "$script_name" ]; then
    green_echo "[!] Script name required"
    return 1
  fi
  
  # Find the script in cache
  local cached_script=""
  for category in install tools exercises uninstall; do
    local category_path="$cache_dir/$category/$script_name"
    if [ -f "$category_path" ]; then
      cached_script="$category_path"
      break
    fi
  done
  
  if [ -z "$cached_script" ]; then
    green_echo "[!] Script not found in cache: $script_name"
    return 1
  fi
  
  echo
  read -rp "Remove $script_name from cache? [y/N]: " confirm
  
  if [[ "${confirm,,}" == "y" ]]; then
    rm -f "$cached_script"
    green_echo "[+] Removed $script_name from cache"
    
    # Refresh script arrays after removal
    load_scripts_from_manifest
  else
    green_echo "[*] Removal cancelled"
  fi
}

count_cached_scripts() {
  local count=0
  if [ -d "$SCRIPT_CACHE_DIR" ]; then
    count=$(find "$SCRIPT_CACHE_DIR" -name "*.sh" -type f 2>/dev/null | wc -l)
  fi
  echo "$count"
}

update_all_scripts() {
  if [ "$REPO_UPDATES_AVAILABLE" -eq 0 ]; then
    green_echo "[*] No updates available"
    return 0
  fi
  
  green_echo "[*] Updating $REPO_UPDATES_AVAILABLE cached scripts..."
  
  # Get list of all cached scripts
  local updated_count=0
  local error_count=0
  
  if [ ! -d "$SCRIPT_CACHE_DIR" ]; then
    green_echo "[!] No script cache directory found"
    return 1
  fi
  
  # Find all cached scripts
  local cached_scripts=$(find "$SCRIPT_CACHE_DIR" -name "*.sh" -type f 2>/dev/null)
  
  if [ -z "$cached_scripts" ]; then
    green_echo "[!] No cached scripts found to update"
    return 1
  fi
  
  while IFS= read -r cached_file; do
    if [ -z "$cached_file" ]; then continue; fi
    
    local script_name=$(basename "$cached_file")
    local script_id="${script_name%.sh}"
    
    green_echo "[*] Updating $script_name..."
    
    if download_script "$script_id"; then
      updated_count=$((updated_count + 1))
      green_echo "[+] Updated $script_name"
    else
      error_count=$((error_count + 1))
      green_echo "[!] Failed to update $script_name"
    fi
  done <<< "$cached_scripts"
  
  green_echo "[+] Update complete: $updated_count updated, $error_count errors"
  
  # Reset updates available counter after successful update
  if [ "$error_count" -eq 0 ]; then
    REPO_UPDATES_AVAILABLE=0
  fi
  
  # Refresh script arrays after updates
  load_scripts_from_manifest
}

check_for_updates() {
  green_echo "[*] Checking for script updates..."
  
  # Fetch latest manifest
  if ! fetch_manifest; then
    green_echo "[!] Failed to fetch latest manifest"
    return 1
  fi
  
  local updates=0
  
  # Compare cached scripts with manifest versions (if available)
  if [ -d "$SCRIPT_CACHE_DIR" ]; then
    local cached_scripts=$(find "$SCRIPT_CACHE_DIR" -name "*.sh" -type f 2>/dev/null)
    if [ -n "$cached_scripts" ]; then
      # For simplicity, assume all cached scripts have updates available
      # In a real implementation, you'd compare timestamps or versions
      updates=$(echo "$cached_scripts" | wc -l)
    fi
  fi
  
  REPO_UPDATES_AVAILABLE="$updates"
  green_echo "[+] Found $updates potential updates"
}

show_repo_settings() {
  while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       Repository Settings                                      ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo
    
    local use_remote=$(get_config_value "use_remote_scripts" "true")
    local auto_check=$(get_config_value "auto_check_updates" "true")
    local auto_install=$(get_config_value "auto_install_updates" "true")
    local interval=$(get_config_value "update_check_interval_minutes" "30")
    local verify_checksums=$(get_config_value "verify_checksums" "true")
    
    local current_manifest_url="${MANIFEST_URL}"
    
    local use_public_repo=$(get_config_value "use_public_repository" "true")
    
    echo "  Current Settings:"
    echo "  1) Use Remote Scripts:      $use_remote"
    echo "  2) Auto-check Updates:      $auto_check"
    echo "  3) Auto-install Updates:    $auto_install"
    echo "  4) Check Interval:          $interval minutes"
    echo "  5) Verify Checksums:        $verify_checksums"
    echo "  6) Use Public Repository:   $use_public_repo"
    echo
    echo "  Options:"
    echo "   r) Toggle remote scripts"
    echo "   c) Toggle auto-check updates"
    echo "   i) Toggle auto-install updates"
    echo "   t) Change check interval"
    echo "   s) Toggle checksum verification"
    echo "   p) Toggle public repository access"
    echo "   v) View repository info"
    echo
    echo "  ──────────────────────────────────────────────────────────────────────────────"
    echo "   b) Back to Repository Menu    0) Exit"
    echo
    
    read -rp "Enter your choice: " settings_choice
    
    case "$settings_choice" in
      r|R)
        if [ "$use_remote" = "true" ]; then
          set_config_value "use_remote_scripts" "false"
          green_echo "[*] Remote scripts disabled"
        else
          set_config_value "use_remote_scripts" "true"
          green_echo "[*] Remote scripts enabled"
        fi
        read -rp "Press Enter to continue..."
        ;;
      c|C)
        if [ "$auto_check" = "true" ]; then
          set_config_value "auto_check_updates" "false"
          green_echo "[*] Auto-check updates disabled"
        else
          set_config_value "auto_check_updates" "true"
          green_echo "[*] Auto-check updates enabled"
        fi
        read -rp "Press Enter to continue..."
        ;;
      i|I)
        if [ "$auto_install" = "true" ]; then
          set_config_value "auto_install_updates" "false"
          green_echo "[*] Auto-install updates disabled"
        else
          set_config_value "auto_install_updates" "true"
          green_echo "[*] Auto-install updates enabled"
        fi
        read -rp "Press Enter to continue..."
        ;;
      s|S)
        if [ "$verify_checksums" = "true" ]; then
          set_config_value "verify_checksums" "false"
          green_echo "[*] Checksum verification disabled"
          green_echo "[!] Warning: This reduces security. Only disable for custom repositories with incorrect checksums."
        else
          set_config_value "verify_checksums" "true"
          green_echo "[*] Checksum verification enabled (recommended)"
        fi
        read -rp "Press Enter to continue..."
        ;;
      t|T)
        echo
        read -rp "Enter new check interval (minutes, 1-1440): " new_interval
        if [[ "$new_interval" =~ ^[0-9]+$ ]] && [ "$new_interval" -ge 1 ] && [ "$new_interval" -le 1440 ]; then
          set_config_value "update_check_interval_minutes" "$new_interval"
          green_echo "[*] Check interval updated to $new_interval minutes"
        else
          green_echo "[!] Invalid interval. Please enter a number between 1 and 1440"
        fi
        read -rp "Press Enter to continue..."
        ;;
      v|V)
        clear
        echo "╔════════════════════════════════════════════════════════════════════════════════╗"
        echo "║                         Repository Information                                 ║"
        echo "╚════════════════════════════════════════════════════════════════════════════════╝"
        echo
        echo "  Repository URL: $REPO_URL"
        echo "  Cache Directory: $SCRIPT_CACHE_DIR"
        echo "  Config File: $CONFIG_FILE"
        echo "  Manifest File: $MANIFEST_FILE"
        echo
        if [ -f "$MANIFEST_FILE" ]; then
          local manifest_version=$(jq -r '.version // "unknown"' "$MANIFEST_FILE" 2>/dev/null)
          local repo_version=$(jq -r '.repository_version // "unknown"' "$MANIFEST_FILE" 2>/dev/null)
          local last_updated=$(jq -r '.last_updated // "unknown"' "$MANIFEST_FILE" 2>/dev/null)
          echo "  Manifest Version: $manifest_version"
          echo "  Repository Version: $repo_version" 
          echo "  Last Updated: $last_updated"
        else
          echo "  Manifest: Not cached"
        fi
        echo
        read -rp "Press Enter to continue..."
        ;;
      p|P)
        # Check if custom manifest is configured
        local has_custom_manifest
        has_custom_manifest=$(get_config_value "custom_manifest_url" "")
        
        if [ "$use_public_repo" = "true" ]; then
          set_config_value "use_public_repository" "false"
          green_echo "[*] Public repository access disabled"
          
          if [ -n "$has_custom_manifest" ]; then
            green_echo "[*] Using custom manifest"
          else
            green_echo "[*] No scripts available (configure custom manifest)"
          fi
        else
          set_config_value "use_public_repository" "true"
          green_echo "[*] Public repository access enabled"
          
          if [ -n "$has_custom_manifest" ]; then
            green_echo "[*] Note: Custom manifest takes priority over public repository"
          else
            green_echo "[*] lv_linux_learn scripts will be available"
          fi
        fi
        
        echo
        green_echo "[*] Note: Custom manifests are managed in the 'Custom Manifests' menu"
        green_echo "[*] The public repository toggle does NOT affect custom manifests"
        read -rp "Press Enter to continue..."
        ;;
      b|B)
        return 0
        ;;
      0)
        green_echo "Exiting. Goodbye!"
        exit 0
        ;;
      *)
        green_echo "[!] Invalid choice"
        read -rp "Press Enter to continue..."
        ;;
    esac
  done
}

# Current menu state
CURRENT_CATEGORY=""

show_main_menu() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       LV Script Manager - Main Menu                            ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Get category counts from manifest (supports dynamic categories)
  declare -A category_counts
  local is_nested
  
  if [ -f "$MANIFEST_CACHE" ] && command -v jq &> /dev/null; then
    # Check if manifest is nested (custom) or flat (public)
    is_nested=$(jq -r '.scripts | type' "$MANIFEST_CACHE" 2>/dev/null)
    
    if [ "$is_nested" = "object" ]; then
      # Custom manifest - nested by category
      local categories
      categories=$(jq -r '.scripts | keys[]' "$MANIFEST_CACHE" 2>/dev/null)
      
      while IFS= read -r category; do
        [ -z "$category" ] && continue
        local count
        count=$(jq -r ".scripts.${category} | length" "$MANIFEST_CACHE" 2>/dev/null || echo "0")
        category_counts[$category]=$count
      done <<< "$categories"
    else
      # Public manifest - flat array
      category_counts[install]=$(jq -r '[.scripts[] | select(.category == "install")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
      category_counts[tools]=$(jq -r '[.scripts[] | select(.category == "tools")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
      category_counts[exercises]=$(jq -r '[.scripts[] | select(.category == "exercises")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
      category_counts[uninstall]=$(jq -r '[.scripts[] | select(.category == "uninstall")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
    fi
  fi
  
  echo "  Select a category:"
  echo
  
  # Standard categories
  local menu_num=1
  printf "   \033[1;32m%d)\033[0m 📦 Install Scripts         (%d scripts)\n" "$menu_num" "${category_counts[install]:-0}"
  echo "      System tools, browsers, development environments"
  echo
  menu_num=$((menu_num + 1))
  
  printf "   \033[1;32m%d)\033[0m 🔧 Tools & Utilities       (%d scripts)\n" "$menu_num" "${category_counts[tools]:-0}"
  echo "      File management, git helpers, conversion tools"
  echo
  menu_num=$((menu_num + 1))
  
  printf "   \033[1;32m%d)\033[0m 📚 Bash Exercises          (%d exercises)\n" "$menu_num" "${category_counts[exercises]:-0}"
  echo "      Learn bash scripting with interactive examples"
  echo
  menu_num=$((menu_num + 1))
  
  printf "   \033[1;32m%d)\033[0m ⚠️  Uninstall               (%d scripts)\n" "$menu_num" "${category_counts[uninstall]:-0}"
  echo "      Remove installed applications and clean configurations"
  echo
  menu_num=$((menu_num + 1))
  
  # Dynamic categories (non-standard)
  declare -a dynamic_categories=()
  declare -A dynamic_category_map
  for category in "${!category_counts[@]}"; do
    if [[ ! "$category" =~ ^(install|tools|exercises|uninstall)$ ]]; then
      dynamic_categories+=("$category")
    fi
  done
  
  # Sort dynamic categories alphabetically
  local dynamic_count="${#dynamic_categories[@]}"
  if [ "$dynamic_count" -gt 0 ]; then
    IFS=$'\n' dynamic_categories=($(sort <<<"${dynamic_categories[*]}"))
    unset IFS
    
    for category in "${dynamic_categories[@]}"; do
      local emoji
      case "${category,,}" in
        custom) emoji="📦" ;;
        ai) emoji="🤖" ;;
        network) emoji="🌐" ;;
        security) emoji="🔒" ;;
        database) emoji="🗄" ;;
        docker) emoji="🐳" ;;
        *) emoji="📝" ;;
      esac
      
      printf "   \033[1;32m%d)\033[0m %s %-22s (%d scripts)\n" "$menu_num" "$emoji" "${category^}" "${category_counts[$category]:-0}"
      echo "      Scripts from custom manifest"
      echo
      dynamic_category_map[$menu_num]="$category"
      menu_num=$((menu_num + 1))
    done
  fi
  
  # Store menu mapping for later use (repository and custom manifests)
  REPO_MENU_NUM=$menu_num
  MANIFEST_MENU_NUM=$((menu_num + 1))
  
  # Show repository option if enabled
  if [ "$REPO_ENABLED" = true ]; then
    local repo_status="enabled"
    if [ "$REPO_UPDATES_AVAILABLE" -gt 0 ]; then
      repo_status="$REPO_UPDATES_AVAILABLE updates available"
    fi
    printf "   \033[1;32m%d)\033[0m 📥 Script Repository       (%s)\n" "$REPO_MENU_NUM" "$repo_status"
    echo "      Download and update scripts from remote repository"
    echo
  fi
  
  # Show custom manifests option (always available)
  printf "   \033[1;32m%d)\033[0m 📁 Custom Manifests       (manifest creator)\n" "$MANIFEST_MENU_NUM"
  echo "      Create and manage custom script collections"
  echo
  
  echo "  ────────────────────────────────────────────────────────────────────────────"
  echo "   h) Help/About    s) Search All    u) Check Updates    0) Exit"
  echo
  
  # Export for main loop
  export DYNAMIC_CATEGORY_MAP
  for key in "${!dynamic_category_map[@]}"; do
    DYNAMIC_CATEGORY_MAP+="${key}:${dynamic_category_map[$key]} "
  done
}

show_menu() {
  local category="$1"
  clear
  
  # Reset display-to-index mapping
  DISPLAY_TO_INDEX=()
  
  local title
  case "$category" in
    install) title="Install Scripts" ;;
    tools) title="Tools & Utilities" ;;
    exercises) title="Bash Exercises" ;;
    uninstall) title="Uninstall" ;;
    custom) title="Custom Scripts" ;;
    *) title="All Scripts" ;;
  esac
  
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  printf "║                       LV Script Manager - %-36s ║\n" "$title"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  
  if [ -n "$SEARCH_FILTER" ]; then
    echo "  🔍 Filter: \"$SEARCH_FILTER\" (press 's' to change/clear)"
  fi
  echo
  
  local display_count=0
  local start_idx=0 end_idx=0
  
  # Determine range based on category
  case "$category" in
    install)
      start_idx=0; end_idx=8
      ;;
    tools)
      start_idx=10; end_idx=20
      ;;
    exercises)
      start_idx=22; end_idx=29
      ;;
    uninstall)
      start_idx=31; end_idx=41
      ;;
    custom)
      # Show only custom scripts
      start_idx=43; end_idx=100
      ;;
  esac
  
  for i in "${!SCRIPTS[@]}"; do
    # Filter by category if specified
    if [ -n "$category" ] && [ "$category" != "custom" ]; then
      if [ "$i" -lt "$start_idx" ] || [ "$i" -gt "$end_idx" ]; then
        continue
      fi
    elif [ "$category" = "custom" ]; then
      # Only show custom scripts (after separator at index 42)
      if [ "$i" -le 42 ]; then
        continue
      fi
    fi
    
    local num=$((i + 1))
    local script="${SCRIPTS[$i]}"
    local desc="${DESCRIPTIONS[$i]}"
    
    # Handle separator entries (empty script path)
    if [ -z "$script" ]; then
      if [ -z "$SEARCH_FILTER" ]; then
        printf "\n  \033[1m%s\033[0m\n" "$desc"
      fi
      continue
    fi
    
    # Apply search filter
    if [ -n "$SEARCH_FILTER" ]; then
      local script_name
      script_name=$(basename "$script" 2>/dev/null || echo "")
      if ! echo "$script_name $desc" | grep -qi "$SEARCH_FILTER"; then
        continue
      fi
    fi
    
    display_count=$((display_count + 1))
    
    # Check if script exists and is executable
    local script_name
    script_name=$(basename "$script" 2>/dev/null || echo "unknown")
    
    # Use display_count for category views, original index for full list
    local show_num
    if [ -n "$category" ]; then
      show_num=$display_count
      # Map display number to actual array index
      DISPLAY_TO_INDEX[$show_num]=$i
    else
      show_num=$num
    fi
    
    # Check cache status
    local cache_status=""
    local script_id=""
    
    # Safely get script ID from array if it exists and has been loaded
    if [ "${#MENU_SCRIPT_IDS[@]}" -gt 0 ] && [ "$i" -lt "${#MENU_SCRIPT_IDS[@]}" ]; then
      script_id="${MENU_SCRIPT_IDS[$i]:-}"
    fi
    
    # Check if script is cached (skip separators and empty IDs)
    if [ -n "$script_id" ] && [ "$script_id" != "__separator__" ] && type get_cached_script_path &> /dev/null; then
      local cached_path=""
      cached_path=$(get_cached_script_path "$script_id" 2>/dev/null || echo "")
      if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
        cache_status=" \033[1;36m[📁 CACHED]\033[0m"
      fi
    fi
    
    # Get file metadata
    local file_info=""
    local actual_file="$script"
    
    # Check if cached version exists and use it for metadata
    if [ -n "$script_id" ] && [ "$script_id" != "__separator__" ] && type get_cached_script_path &> /dev/null; then
      local cached_path=""
      cached_path=$(get_cached_script_path "$script_id" 2>/dev/null || echo "")
      if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
        actual_file="$cached_path"
      fi
    fi
    
    # Extract metadata if file exists
    if [ -f "$actual_file" ]; then
      local size_bytes=$(stat -c%s "$actual_file" 2>/dev/null || echo "0")
      local size_kb=$((size_bytes / 1024))
      local modified=$(stat -c%y "$actual_file" 2>/dev/null | cut -d' ' -f1)
      
      # Get version from manifest if available
      local version=""
      if [ -f "$MANIFEST_CACHE" ] && [ -n "$script_id" ] && [ "$script_id" != "__separator__" ]; then
        version=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .version" "$MANIFEST_CACHE" 2>/dev/null || echo "")
        if [ -n "$version" ] && [ "$version" != "null" ]; then
          file_info=" \033[2m│ v${version}\033[0m"
        fi
      fi
      
      if [ "$size_kb" -gt 0 ]; then
        file_info="${file_info} \033[2m│ ${size_kb}KB\033[0m"
      fi
      if [ -n "$modified" ]; then
        file_info="${file_info} \033[2m│ ${modified}\033[0m"
      fi
    fi
    
    # Format with better alignment and readability
    if [ ! -f "$script" ]; then
      printf "  \033[1;31m%2d)\033[0m \033[0;31m%-30s\033[0m" "$show_num" "$script_name"
      printf " \033[1;31m[MISSING]\033[0m"
      printf "%b\n" "$file_info"
    elif [ ! -x "$script" ]; then
      printf "  \033[1;33m%2d)\033[0m \033[0;33m%-30s\033[0m" "$show_num" "$script_name"
      printf " \033[1;33m[NOT EXEC]\033[0m"
      printf "%b\n" "$file_info"
    else
      printf "  \033[1;32m%2d)\033[0m \033[1m%-30s\033[0m" "$show_num" "$script_name"
      printf "%b" "$cache_status"
      # Add metadata on same line with better spacing
      if [ -n "$file_info" ]; then
        printf "  %b" "$file_info"
      fi
      printf "\n"
    fi
    # Description indented on next line with subtle styling
    printf "      \033[2;3m%s\033[0m\n" "$desc"
  done
  
  if [ -n "$SEARCH_FILTER" ] && [ "$display_count" -eq 0 ]; then
    echo "  No scripts match your search filter."
  fi
  
  echo
  echo "  ────────────────────────────────────────────────────────────────────────────"
  if [ -n "$category" ]; then
    echo "   b) Back to Main Menu    s) Search    0) Exit"
  else
    echo "   h) Help/About    s) Search    0) Exit"
  fi
  echo
}

add_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Add Custom Script                                      ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  green_echo "Type 'cancel' or 'back' at any prompt to exit"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    green_echo "[*] Install it with: sudo apt install jq"
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Ensure config directory exists
  mkdir -p "$CUSTOM_SCRIPTS_DIR/scripts"
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    echo '{"scripts":[]}' > "$CUSTOM_SCRIPTS_JSON"
  fi
  
  # Get script name
  read -rp "Script Name: " script_name
  if [[ "$script_name" == "cancel" || "$script_name" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$script_name" ]; then
    green_echo "[!] Script name cannot be empty"
    sleep 2
    return 1
  fi
  
  # Get script path
  read -rp "Script Path (absolute): " script_path
  if [[ "$script_path" == "cancel" || "$script_path" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$script_path" ]; then
    green_echo "[!] Script path cannot be empty"
    sleep 2
    return 1
  fi
  
  # Validate script exists
  if [ ! -f "$script_path" ]; then
    green_echo "[!] Script file not found: $script_path"
    sleep 2
    return 1
  fi
  
  # Make executable if not already
  if [ ! -x "$script_path" ]; then
    green_echo "[*] Making script executable..."
    chmod +x "$script_path" || {
      green_echo "[!] Failed to make script executable"
      sleep 2
      return 1
    }
  fi
  
  # Get category
  echo
  echo "Select category:"
  echo "  1) Install"
  echo "  2) Tools"
  echo "  3) Exercises"
  echo "  4) Uninstall"
  read -rp "Choice [1-4]: " cat_choice
  
  if [[ "$cat_choice" == "cancel" || "$cat_choice" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  
  case "$cat_choice" in
    1) category="install" ;;
    2) category="tools" ;;
    3) category="exercises" ;;
    4) category="uninstall" ;;
    *)
      green_echo "[!] Invalid category"
      sleep 2
      return 1
      ;;
  esac
  
  # Get description
  echo
  green_echo "Enter description (one line, or press Enter to skip):"
  read -r description
  if [[ "$description" == "cancel" || "$description" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  if [ -z "$description" ]; then
    description="Custom script"
  fi
  
  # Get sudo requirement
  read -rp "Requires sudo? [y/N]: " needs_sudo
  if [[ "$needs_sudo" == "cancel" || "$needs_sudo" == "back" ]]; then
    green_echo "[*] Cancelled"
    sleep 1
    return 0
  fi
  requires_sudo="false"
  if [[ "$needs_sudo" =~ ^[Yy] ]]; then
    requires_sudo="true"
  fi
  
  # Generate UUID
  script_id=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)
  created_date=$(date -Iseconds)
  
  # Add to JSON
  local temp_json
  temp_json=$(mktemp)
  jq --arg id "$script_id" \
     --arg name "$script_name" \
     --arg category "$category" \
     --arg path "$script_path" \
     --arg desc "$description" \
     --argjson sudo "$requires_sudo" \
     --arg date "$created_date" \
     '.scripts += [{
       id: $id,
       name: $name,
       category: $category,
       script_path: $path,
       description: $desc,
       requires_sudo: $sudo,
       created_date: $date,
       is_custom: true
     }]' "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script added successfully!"
  # DEPRECATED: Custom scripts no longer reloaded separately
  # green_echo "[*] Reloading custom scripts..."
  # reload_custom_scripts
  sleep 1
}

edit_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Edit Custom Script                                     ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Check if custom scripts exist
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    green_echo "[!] No custom scripts found."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  local script_count
  script_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON")
  
  if [ "$script_count" -eq 0 ]; then
    green_echo "[!] No custom scripts to edit."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # List custom scripts
  green_echo "Custom Scripts:"
  echo
  jq -r '.scripts[] | "\(.name) - \(.category)"' "$CUSTOM_SCRIPTS_JSON" | nl -w2 -s') '
  echo
  
  read -rp "Enter script number to edit (or 'cancel'): " script_num
  
  if [[ "$script_num" == "cancel" || "$script_num" == "back" ]]; then
    return 0
  fi
  
  if ! [[ "$script_num" =~ ^[0-9]+$ ]] || [ "$script_num" -lt 1 ] || [ "$script_num" -gt "$script_count" ]; then
    green_echo "[!] Invalid script number"
    sleep 2
    return 1
  fi
  
  # Get script details (jq arrays are 0-indexed)
  local idx=$((script_num - 1))
  local script_id
  script_id=$(jq -r ".scripts[$idx].id" "$CUSTOM_SCRIPTS_JSON")
  
  green_echo "[*] Editing: $(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")"
  green_echo "Type 'cancel' or 'back' at any prompt to exit"
  green_echo "Press Enter to keep current value"
  echo
  
  # Get new values or keep existing
  local current_name current_category current_path current_desc current_sudo
  current_name=$(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")
  current_category=$(jq -r ".scripts[$idx].category" "$CUSTOM_SCRIPTS_JSON")
  current_path=$(jq -r ".scripts[$idx].script_path" "$CUSTOM_SCRIPTS_JSON")
  current_desc=$(jq -r ".scripts[$idx].description" "$CUSTOM_SCRIPTS_JSON")
  current_sudo=$(jq -r ".scripts[$idx].requires_sudo" "$CUSTOM_SCRIPTS_JSON")
  
  read -rp "Script Name [$current_name]: " new_name
  if [[ "$new_name" == "cancel" || "$new_name" == "back" ]]; then return 0; fi
  [ -z "$new_name" ] && new_name="$current_name"
  
  read -rp "Script Path [$current_path]: " new_path
  if [[ "$new_path" == "cancel" || "$new_path" == "back" ]]; then return 0; fi
  [ -z "$new_path" ] && new_path="$current_path"
  
  # Validate new path if changed
  if [ "$new_path" != "$current_path" ] && [ ! -f "$new_path" ]; then
    green_echo "[!] Warning: Script file not found: $new_path"
    read -rp "Continue anyway? [y/N]: " continue_edit
    if [[ ! "${continue_edit,,}" == "y" ]]; then
      return 1
    fi
  fi
  
  echo
  echo "Category: 1) install  2) tools  3) exercises  4) uninstall"
  read -rp "Category [$current_category]: " new_category_num
  if [[ "$new_category_num" == "cancel" || "$new_category_num" == "back" ]]; then return 0; fi
  
  local new_category="$current_category"
  if [ -n "$new_category_num" ]; then
    case "$new_category_num" in
      1) new_category="install" ;;
      2) new_category="tools" ;;
      3) new_category="exercises" ;;
      4) new_category="uninstall" ;;
      *) green_echo "[!] Invalid category, keeping current"; new_category="$current_category" ;;
    esac
  fi
  
  read -rp "Description [$current_desc]: " new_desc
  if [[ "$new_desc" == "cancel" || "$new_desc" == "back" ]]; then return 0; fi
  [ -z "$new_desc" ] && new_desc="$current_desc"
  
  read -rp "Requires sudo? [y/N] (current: $current_sudo): " new_sudo_input
  if [[ "$new_sudo_input" == "cancel" || "$new_sudo_input" == "back" ]]; then return 0; fi
  
  local new_sudo="$current_sudo"
  if [ -n "$new_sudo_input" ]; then
    if [[ "$new_sudo_input" =~ ^[Yy] ]]; then
      new_sudo="true"
    else
      new_sudo="false"
    fi
  fi
  
  # Update the script in JSON
  local temp_json
  temp_json=$(mktemp)
  jq --arg id "$script_id" \
     --arg name "$new_name" \
     --arg category "$new_category" \
     --arg path "$new_path" \
     --arg desc "$new_desc" \
     --argjson sudo "$new_sudo" \
     '(.scripts[] | select(.id == $id)) |= {
       id: $id,
       name: $name,
       category: $category,
       script_path: $path,
       description: $desc,
       requires_sudo: $sudo,
       created_date: .created_date,
       is_custom: true
     }' "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script updated successfully!"
  # DEPRECATED: Custom scripts no longer reloaded separately
  # green_echo "[*] Reloading custom scripts..."
  # reload_custom_scripts
  sleep 1
}

delete_custom_script() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Delete Custom Script                                   ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Check if jq is installed
  if ! command -v jq &> /dev/null; then
    green_echo "[!] Error: 'jq' is required for custom script management."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # Check if custom scripts exist
  if [ ! -f "$CUSTOM_SCRIPTS_JSON" ]; then
    green_echo "[!] No custom scripts found."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  local script_count
  script_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON")
  
  if [ "$script_count" -eq 0 ]; then
    green_echo "[!] No custom scripts to delete."
    read -rp "Press Enter to continue..."
    return 1
  fi
  
  # List custom scripts
  green_echo "Custom Scripts:"
  echo
  jq -r '.scripts[] | "\(.name) - \(.category) - \(.script_path)"' "$CUSTOM_SCRIPTS_JSON" | nl -w2 -s') '
  echo
  
  read -rp "Enter script number to delete (or 'cancel'): " script_num
  
  if [[ "$script_num" == "cancel" || "$script_num" == "back" ]]; then
    return 0
  fi
  
  if ! [[ "$script_num" =~ ^[0-9]+$ ]] || [ "$script_num" -lt 1 ] || [ "$script_num" -gt "$script_count" ]; then
    green_echo "[!] Invalid script number"
    sleep 2
    return 1
  fi
  
  # Get script details for confirmation
  local idx=$((script_num - 1))
  local script_name
  script_name=$(jq -r ".scripts[$idx].name" "$CUSTOM_SCRIPTS_JSON")
  
  echo
  green_echo "[!] WARNING: This will permanently delete: $script_name"
  read -rp "Are you sure? [y/N]: " confirm
  
  if [[ ! "${confirm,,}" == "y" ]]; then
    green_echo "[*] Deletion cancelled"
    sleep 1
    return 0
  fi
  
  # Delete the script from JSON
  local temp_json
  temp_json=$(mktemp)
  jq "del(.scripts[$idx])" "$CUSTOM_SCRIPTS_JSON" > "$temp_json" && mv "$temp_json" "$CUSTOM_SCRIPTS_JSON"
  
  green_echo "[+] Custom script deleted successfully!"
  # DEPRECATED: Custom scripts no longer reloaded separately
  # green_echo "[*] Reloading custom scripts..."
  # reload_custom_scripts
  sleep 1
}

show_repository_menu() {
  if [ "$REPO_ENABLED" != true ]; then
    green_echo "[!] Repository system not available"
    sleep 2
    return 1
  fi
  
  while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       Script Repository Manager                                ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo
    
    local total_scripts=$(jq -r '.scripts | length' "$MANIFEST_FILE" 2>/dev/null || echo "0")
    local cached_count=$(count_cached_scripts)
    local updates="$REPO_UPDATES_AVAILABLE"
    
    echo "  Repository Status:"
    echo "  • Available scripts: $total_scripts"
    echo "  • Cached locally:    $cached_count"
    echo "  • Updates available: $updates"
    echo
    echo "  ────────────────────────────────────────────────────────────────────────────"
    echo
    echo "  Options:"
    printf "   \033[1;32m1)\033[0m Update All Scripts         ($updates updates)\n"
    echo "   2) Download All Scripts        (bulk download)"
    echo "   3) Download Single Script      (browse and select)"
    echo "   4) View Cached Scripts         (list local cache)"
    echo "   5) Clear Script Cache          (remove all cached)"
    echo "   6) Check for Updates           (manual refresh)"
    echo "   7) Repository Settings"
    echo
    echo "  ──────────────────────────────────────────────────────────────────────────────"
    echo "   b) Back to Main Menu    0) Exit"
    echo
    
    read -rp "Enter your choice: " repo_choice
    
    case "$repo_choice" in
      1)
        update_all_scripts
        read -rp "Press Enter to continue..."
        ;;
      2)
        green_echo "[*] This will download all $total_scripts scripts from the repository."
        read -rp "Continue? [y/N]: " confirm
        if [[ "${confirm,,}" == "y" ]]; then
          download_all_scripts
        fi
        read -rp "Press Enter to continue..."
        ;;
      3)
        download_single_script
        read -rp "Press Enter to continue..."
        ;;
      4)
        clear
        list_cached_scripts
        read -rp "Press Enter to continue..."
        ;;
      5)
        clear_script_cache
        read -rp "Press Enter to continue..."
        ;;
      6)
        green_echo "[*] Checking for updates..."
        check_for_updates
        green_echo "[+] Update check complete. $REPO_UPDATES_AVAILABLE updates available."
        read -rp "Press Enter to continue..."
        ;;
      7)
        show_repo_settings
        ;;
      b|B)
        return 0
        ;;
      0)
        green_echo "Exiting. Goodbye!"
        exit 0
        ;;
      *)
        green_echo "[!] Invalid choice"
        sleep 1
        ;;
    esac
  done
}



show_help() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       LV Script Manager - Help                                 ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  green_echo "ABOUT"
  echo "  LV Script Manager - A curated collection of Ubuntu setup scripts and utilities"
  echo "  Repository: https://github.com/amatson97/lv_linux_learn"
  echo "  License: MIT"
  echo
  green_echo "USAGE"
  echo "  • Select a script number to run it"
  echo "  • Press 'a' to add your own custom scripts"
  echo "  • Press 's' to search/filter scripts"
  echo "  • Press 'h' to see this help screen"
  echo "  • Press '0' to exit"
  echo
  green_echo "CUSTOM SCRIPTS"
  echo "  • Add your own scripts without editing code"
  echo "  • Scripts are stored in: ~/.lv_linux_learn/"
  echo "  • Custom scripts marked with 📝 emoji"
  echo "  • Requires 'jq' package: sudo apt install jq"
  echo
  green_echo "SCRIPT REPOSITORY"
  echo "  • Access via 'Script Repository' menu option"
  echo "  • Download scripts to local cache for faster execution"
  echo "  • Download all scripts or select individual scripts"
  echo "  • Automatic update checking and version management"
  echo "  • Scripts cached in: ~/.lv_linux_learn/script_cache/"
  echo
  green_echo "TABS/CATEGORIES"
  echo "  • Install: System tools and applications"
  echo "  • Tools: Utility scripts for file management and tasks"
  echo "  • Exercises: Bash learning exercises"
  echo "  • Uninstall: Safely remove installed tools"
  echo
  green_echo "DOCUMENTATION"
  echo "  • Quick Start: $script_dir/README.md"
  echo "  • Custom Scripts: $script_dir/docs/CUSTOM_SCRIPTS.md"
  echo "  • Bash Exercises: $script_dir/bash_exercises/"
  echo
  green_echo "SUPPORT"
  echo "  • GitHub Issues: https://github.com/amatson97/lv_linux_learn/issues"
  echo "  • Target Environment: Ubuntu 24.04.3 LTS Desktop"
  echo
  read -rp "Press Enter to return to menu..."
}

search_scripts() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                         Search/Filter Scripts                                  ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  if [ -n "$SEARCH_FILTER" ]; then
    echo "  Current filter: \"$SEARCH_FILTER\""
    echo
  fi
  
  read -rp "Enter search term (or leave empty to clear): " new_filter
  SEARCH_FILTER="$new_filter"
  
  if [ -n "$SEARCH_FILTER" ]; then
    green_echo "[*] Filter applied: \"$SEARCH_FILTER\""
  else
    green_echo "[*] Filter cleared"
  fi
  sleep 1
}

run_script() {
  local script="$1"
  local script_name
  script_name="$(basename "$script")"
  
  # Priority 1: Always check if script is available in cache first
  if [ "$REPO_ENABLED" = "true" ] && command -v get_cached_script_path &> /dev/null; then
    # Try to find script ID from manifest
    local script_id=""
    if [ -f "$MANIFEST_CACHE" ]; then
      script_id=$(jq -r ".scripts[] | select(.relative_path | endswith(\"$script_name\")) | .id" "$MANIFEST_CACHE" 2>/dev/null | head -1)
    fi
    
    if [ -n "$script_id" ] && [ "$script_id" != "null" ]; then
      # Check if script is already cached
      local cached_path=$(get_cached_script_path "$script_id" 2>/dev/null)
      
      if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
        # Script is cached - use cached version
        green_echo "[*] Using cached version of $script_name"
        script="$cached_path"
      else
        # Script not cached - offer to download to cache
        echo
        green_echo "[!] $script_name is not in cache"
        echo "This script is available in the repository and can be downloaded to cache."
        read -rp "Download $script_name to cache and run? [y/N]: " download_choice
        
        if [[ "${download_choice,,}" == "y" ]]; then
          green_echo "[*] Downloading $script_name to cache..."
          
          if download_script "$script_id"; then
            green_echo "[+] Downloaded successfully to cache!"
            
            # Get the cached script path and use it
            cached_path=$(get_cached_script_path "$script_id")
            if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
              script="$cached_path"
              green_echo "[*] Running from cache..."
            else
              green_echo "[!] Error: Could not locate downloaded script in cache"
              return 1
            fi
          else
            green_echo "[!] Download failed"
            # Fall back to local version if it exists
            if [ -f "$script" ]; then
              green_echo "[*] Falling back to local version..."
            else
              green_echo "[!] Cannot run script - not cached and download failed"
              return 1
            fi
          fi
        else
          # User declined download - fall back to local version if it exists
          if [ -f "$script" ]; then
            green_echo "[*] Using local version (not cached)"
          else
            green_echo "[!] Script not found locally and download declined"
            return 1
          fi
        fi
      fi
    else
      # Script not in manifest - fall back to local version if it exists
      if [ ! -f "$script" ]; then
        green_echo "[!] Error: Script not found: $script"
        return 1
      fi
      green_echo "[*] Script not in repository manifest, using local version"
    fi
  else
    # Repository not enabled or functions not available - use local version
    if [ ! -f "$script" ]; then
      green_echo "[!] Error: Script not found: $script"
      return 1
    fi
    green_echo "[*] Repository system not available, using local version"
  fi
  
  # Check if this is a cached script that needs special handling
  if [[ "$script" == *"/.lv_linux_learn/script_cache/"* ]]; then
    # Cached script - ensure includes directory is available
    ensure_includes_available || {
      green_echo "[!] Warning: Could not ensure includes availability for cached script"
    }
    green_echo "[*] Executing cached script with includes support..."
  fi
  
  if [ ! -x "$script" ]; then
    green_echo "[!] Warning: Script is not executable. Making it executable..."
    chmod +x "$script" || {
      green_echo "[!] Error: Failed to make script executable. Running with bash..."
      bash "$script"
      return $?
    }
  fi
  
  green_echo "[*] Running $script_name..."
  echo "────────────────────────────────────────────────────────────────────────────────"
  
  # Run script - check if absolute or relative path
  local exit_code=0
  if [[ "$script" = /* ]]; then
    # Absolute path - run directly
    "$script" || exit_code=$?
  else
    # Relative path - run with ./
    ./"$script" || exit_code=$?
  fi
  
  echo "────────────────────────────────────────────────────────────────────────────────"
  if [ $exit_code -eq 0 ]; then
    green_echo "[+] $script_name completed successfully"
  else
    green_echo "[!] $script_name exited with code $exit_code"
    return $exit_code
  fi
}

# ============================================================================
# Custom Manifest Management Functions
# ============================================================================

show_custom_manifest_menu() {
  while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       Custom Manifest Manager                                  ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════╝"
    echo
    
    # Show current manifest status
    show_current_manifest_status
    echo
    
    # Show available custom manifests
    local custom_manifests_dir="$HOME/.lv_linux_learn/custom_manifests"
    local manifest_count=0
    if [ -d "$custom_manifests_dir" ]; then
      manifest_count=$(find "$custom_manifests_dir" -name "manifest.json" | wc -l)
    fi
    
    echo "  Available Custom Manifests: $manifest_count"
    echo
    echo "  Options:"
    echo "   1) Create New Custom Manifest     (scan directories for scripts)"
    echo "   2) List Custom Manifests          (show all created manifests)"
    echo "   3) Switch to Custom Manifest      (activate a custom manifest)"
    echo "   4) Switch to Default Manifest     (return to GitHub repository)"
    echo "   5) Delete Custom Manifest         (permanently remove)"
    echo
    echo "  ──────────────────────────────────────────────────────────────────────────────"
    echo "   b) Back to Main Menu    0) Exit"
    echo
    
    read -rp "Enter your choice: " cm_choice
    
    case "$cm_choice" in
      1)
        create_custom_manifest_interactive
        read -rp "Press Enter to continue..."
        ;;
      2)
        list_custom_manifests
        read -rp "Press Enter to continue..."
        ;;
      3)
        switch_to_custom_manifest_interactive
        read -rp "Press Enter to continue..."
        ;;
      4)
        switch_to_default_manifest
        read -rp "Press Enter to continue..."
        ;;
      5)
        delete_custom_manifest_interactive
        read -rp "Press Enter to continue..."
        ;;
      b|B)
        return 0
        ;;
      0)
        green_echo "Exiting. Goodbye!"
        exit 0
        ;;
      *)
        green_echo "[!] Invalid choice"
        sleep 1
        ;;
    esac
  done
}

show_current_manifest_status() {
  echo "  Current Manifest Status:"
  
  # Check if custom manifest URL is set
  local custom_url=""
  if [ -n "${CUSTOM_MANIFEST_URL:-}" ]; then
    custom_url="$CUSTOM_MANIFEST_URL"
  elif command -v jq &> /dev/null && [ -f "$CONFIG_DIR/config.json" ]; then
    custom_url=$(jq -r '.custom_manifest_url // ""' "$CONFIG_DIR/config.json" 2>/dev/null)
  fi
  
  if [ -n "$custom_url" ]; then
    if [[ "$custom_url" == file://* ]]; then
      # Local custom manifest
      local manifest_path="${custom_url#file://}"
      if [ -f "$manifest_path" ] && command -v jq &> /dev/null; then
        local manifest_name=$(jq -r '.repository_name // "Unknown"' "$manifest_path" 2>/dev/null)
        local total_scripts=$(jq -r '.total_scripts // 0' "$manifest_path" 2>/dev/null)
        echo "  • Active: $manifest_name (Custom Local - $total_scripts scripts)"
      else
        echo "  • Active: Custom Local Manifest (file not found)"
      fi
    else
      # Remote custom manifest
      echo "  • Active: Custom Remote Repository"
      echo "  • URL: $custom_url"
    fi
  else
    # Default manifest
    echo "  • Active: LV Linux Learn (Default GitHub Repository)"
  fi
}

create_custom_manifest_interactive() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       Create Custom Manifest                                   ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  # Get manifest name
  while true; do
    read -rp "Manifest name (alphanumeric, hyphens, underscores only): " manifest_name
    
    if [ -z "$manifest_name" ]; then
      green_echo "[!] Please enter a manifest name"
      continue
    fi
    
    # Validate name (only alphanumeric, hyphens, underscores)
    if [[ ! "$manifest_name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
      green_echo "[!] Name must contain only letters, numbers, hyphens, and underscores"
      continue
    fi
    
    # Check if manifest already exists
    local manifest_dir="$HOME/.lv_linux_learn/custom_manifests/$manifest_name"
    if [ -d "$manifest_dir" ]; then
      green_echo "[!] Manifest '$manifest_name' already exists"
      continue
    fi
    
    break
  done
  
  # Get description
  read -rp "Description (optional): " description
  if [ -z "$description" ]; then
    description="Custom script collection: $manifest_name"
  fi
  
  # Get recursive option
  echo
  echo "Scan directories recursively? This will search subdirectories for scripts."
  read -rp "Recursive scan [Y/n]: " recursive_choice
  local recursive="true"
  if [[ "${recursive_choice,,}" == "n" ]]; then
    recursive="false"
  fi
  
  # Collect directories
  local directories=()
  echo
  echo "Add directories to scan for scripts:"
  echo "(Enter full paths, press Enter with empty line when done)"
  
  while true; do
    read -rp "Directory path (or Enter to finish): " dir_path
    
    if [ -z "$dir_path" ]; then
      break
    fi
    
    # Expand tilde
    dir_path="${dir_path/#\~/$HOME}"
    
    if [ ! -d "$dir_path" ]; then
      green_echo "[!] Directory does not exist: $dir_path"
      continue
    fi
    
    directories+=("$dir_path")
    green_echo "[+] Added: $dir_path"
  done
  
  if [ ${#directories[@]} -eq 0 ]; then
    green_echo "[!] No directories specified. Cancelling."
    return 1
  fi
  
  # Create the manifest using Python
  echo
  green_echo "[*] Creating custom manifest '$manifest_name'..."
  green_echo "[*] Scanning directories: ${directories[*]}"
  
  # Use Python to create the manifest
  if command -v python3 &> /dev/null; then
    local python_script="
import sys
import os
sys.path.insert(0, os.path.join('$script_dir', 'lib'))

try:
    from custom_manifest import CustomManifestCreator
    creator = CustomManifestCreator()
    
    directories = ['${directories[@]}']
    success, message = creator.create_manifest(
        '$manifest_name', 
        directories, 
        '$description', 
        $recursive
    )
    
    if success:
        print(f'SUCCESS: {message}')
        exit(0)
    else:
        print(f'ERROR: {message}')
        exit(1)
        
except Exception as e:
    print(f'ERROR: Failed to create manifest: {e}')
    exit(1)
"
    
    local result
    result=$(python3 -c "$python_script" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
      green_echo "[+] ${result#SUCCESS: }"
      echo
      echo "Manifest '$manifest_name' created successfully!"
      echo "You can now switch to it using option 3 in this menu."
    else
      green_echo "[!] ${result#ERROR: }"
    fi
  else
    green_echo "[!] Error: Python3 is required for custom manifest creation"
    green_echo "    Install with: sudo apt install python3"
  fi
}

list_custom_manifests() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       Custom Manifests List                                    ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  local custom_manifests_dir="$HOME/.lv_linux_learn/custom_manifests"
  
  if [ ! -d "$custom_manifests_dir" ]; then
    echo "  No custom manifests found."
    echo "  Use option 1 to create your first custom manifest."
    return 0
  fi
  
  local count=0
  for manifest_dir in "$custom_manifests_dir"/*; do
    if [ ! -d "$manifest_dir" ]; then
      continue
    fi
    
    local manifest_file="$manifest_dir/manifest.json"
    if [ ! -f "$manifest_file" ]; then
      continue
    fi
    
    count=$((count + 1))
    local manifest_name=$(basename "$manifest_dir")
    
    echo "  $count) $manifest_name"
    
    if command -v jq &> /dev/null; then
      local description=$(jq -r '.repository_description // "No description"' "$manifest_file" 2>/dev/null)
      local total_scripts=$(jq -r '.total_scripts // 0' "$manifest_file" 2>/dev/null)
      local created=$(jq -r '.created // "Unknown"' "$manifest_file" 2>/dev/null)
      
      # Format created date
      local created_formatted="$created"
      if [[ "$created" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T ]]; then
        created_formatted="${created:0:16}"  # Just YYYY-MM-DD HH:MM
      fi
      
      echo "     Description: $description"
      echo "     Scripts: $total_scripts"
      echo "     Created: $created_formatted"
    else
      echo "     (Install 'jq' package to see details)"
    fi
    echo
  done
  
  if [ $count -eq 0 ]; then
    echo "  No custom manifests found."
    echo "  Use option 1 to create your first custom manifest."
  else
    echo "  Total: $count custom manifest(s)"
  fi
}

switch_to_custom_manifest_interactive() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       Switch to Custom Manifest                                ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  local custom_manifests_dir="$HOME/.lv_linux_learn/custom_manifests"
  
  if [ ! -d "$custom_manifests_dir" ]; then
    echo "  No custom manifests found."
    echo "  Use option 1 to create a custom manifest first."
    return 0
  fi
  
  # Build array of manifest names
  local manifest_names=()
  local count=0
  
  for manifest_dir in "$custom_manifests_dir"/*; do
    if [ ! -d "$manifest_dir" ]; then
      continue
    fi
    
    local manifest_file="$manifest_dir/manifest.json"
    if [ ! -f "$manifest_file" ]; then
      continue
    fi
    
    count=$((count + 1))
    local manifest_name=$(basename "$manifest_dir")
    manifest_names+=("$manifest_name")
    
    echo "  $count) $manifest_name"
    
    if command -v jq &> /dev/null; then
      local description=$(jq -r '.repository_description // "No description"' "$manifest_file" 2>/dev/null)
      local total_scripts=$(jq -r '.total_scripts // 0' "$manifest_file" 2>/dev/null)
      echo "     $description ($total_scripts scripts)"
    fi
  done
  
  if [ $count -eq 0 ]; then
    echo "  No custom manifests found."
    return 0
  fi
  
  echo
  read -rp "Select manifest to switch to (1-$count, or 0 to cancel): " choice
  
  if [[ "$choice" == "0" ]]; then
    return 0
  fi
  
  if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt $count ]; then
    green_echo "[!] Invalid choice"
    return 1
  fi
  
  local selected_manifest="${manifest_names[$((choice-1))]}"
  
  echo
  green_echo "[*] Switching to manifest: $selected_manifest"
  
  # Use Python to switch manifest
  if command -v python3 &> /dev/null; then
    local python_script="
import sys
import os
sys.path.insert(0, os.path.join('$script_dir', 'lib'))

try:
    from custom_manifest import CustomManifestCreator
    creator = CustomManifestCreator()
    
    success, message = creator.switch_to_custom_manifest('$selected_manifest')
    
    if success:
        print(f'SUCCESS: {message}')
        exit(0)
    else:
        print(f'ERROR: {message}')
        exit(1)
        
except Exception as e:
    print(f'ERROR: Failed to switch manifest: {e}')
    exit(1)
"
    
    local result
    result=$(python3 -c "$python_script" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
      green_echo "[+] ${result#SUCCESS: }"
      echo
      echo "Successfully switched to custom manifest: $selected_manifest"
      echo "The application will now use this manifest for script operations."
      echo "Use option 4 to switch back to the default manifest if needed."
      
      # Clear cached manifest to force reload
      if [ -f "$MANIFEST_CACHE" ]; then
        rm -f "$MANIFEST_CACHE"
      fi
      
      # Update environment variable
      export CUSTOM_MANIFEST_URL="file://$custom_manifests_dir/$selected_manifest/manifest.json"
    else
      green_echo "[!] ${result#ERROR: }"
    fi
  else
    green_echo "[!] Error: Python3 is required for manifest switching"
    green_echo "    Install with: sudo apt install python3"
  fi
}

switch_to_default_manifest() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       Switch to Default Manifest                               ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  echo "  This will switch back to the default LV Linux Learn repository."
  echo "  Your custom manifests will not be deleted."
  echo
  read -rp "Continue? [y/N]: " confirm
  
  if [[ "${confirm,,}" != "y" ]]; then
    green_echo "[*] Cancelled"
    return 0
  fi
  
  green_echo "[*] Switching to default manifest..."
  
  # Use Python to switch to default
  if command -v python3 &> /dev/null; then
    local python_script="
import sys
import os
sys.path.insert(0, os.path.join('$script_dir', 'lib'))

try:
    from custom_manifest import CustomManifestCreator
    creator = CustomManifestCreator()
    
    success, message = creator.switch_to_default_manifest()
    
    if success:
        print(f'SUCCESS: {message}')
        exit(0)
    else:
        print(f'ERROR: {message}')
        exit(1)
        
except Exception as e:
    print(f'ERROR: Failed to switch to default: {e}')
    exit(1)
"
    
    local result
    result=$(python3 -c "$python_script" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
      green_echo "[+] ${result#SUCCESS: }"
      echo
      echo "Successfully switched to default manifest."
      
      # Clear environment variable
      unset CUSTOM_MANIFEST_URL
      
      # Clear cached manifest to force reload
      if [ -f "$MANIFEST_CACHE" ]; then
        rm -f "$MANIFEST_CACHE"
      fi
    else
      green_echo "[!] ${result#ERROR: }"
    fi
  else
    green_echo "[!] Error: Python3 is required for manifest switching"
    green_echo "    Install with: sudo apt install python3"
  fi
}

delete_custom_manifest_interactive() {
  clear
  echo "╔════════════════════════════════════════════════════════════════════════════════╗"
  echo "║                       Delete Custom Manifest                                   ║"
  echo "╚════════════════════════════════════════════════════════════════════════════════╝"
  echo
  
  local custom_manifests_dir="$HOME/.lv_linux_learn/custom_manifests"
  
  if [ ! -d "$custom_manifests_dir" ]; then
    echo "  No custom manifests found."
    return 0
  fi
  
  # Build array of manifest names
  local manifest_names=()
  local count=0
  
  for manifest_dir in "$custom_manifests_dir"/*; do
    if [ ! -d "$manifest_dir" ]; then
      continue
    fi
    
    local manifest_file="$manifest_dir/manifest.json"
    if [ ! -f "$manifest_file" ]; then
      continue
    fi
    
    count=$((count + 1))
    local manifest_name=$(basename "$manifest_dir")
    manifest_names+=("$manifest_name")
    
    echo "  $count) $manifest_name"
    
    if command -v jq &> /dev/null; then
      local description=$(jq -r '.repository_description // "No description"' "$manifest_file" 2>/dev/null)
      local total_scripts=$(jq -r '.total_scripts // 0' "$manifest_file" 2>/dev/null)
      echo "     $description ($total_scripts scripts)"
    fi
  done
  
  if [ $count -eq 0 ]; then
    echo "  No custom manifests found."
    return 0
  fi
  
  echo
  read -rp "Select manifest to DELETE (1-$count, or 0 to cancel): " choice
  
  if [[ "$choice" == "0" ]]; then
    return 0
  fi
  
  if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt $count ]; then
    green_echo "[!] Invalid choice"
    return 1
  fi
  
  local selected_manifest="${manifest_names[$((choice-1))]}"
  
  echo
  green_echo "[!] WARNING: This will permanently delete manifest '$selected_manifest'"
  echo "  This will remove the manifest and all its copied scripts."
  echo
  read -rp "Type 'DELETE' to confirm: " confirm
  
  if [ "$confirm" != "DELETE" ]; then
    green_echo "[*] Cancelled"
    return 0
  fi
  
  green_echo "[*] Deleting manifest: $selected_manifest"
  
  # Use Python to delete manifest
  if command -v python3 &> /dev/null; then
    local python_script="
import sys
import os
sys.path.insert(0, os.path.join('$script_dir', 'lib'))

try:
    from custom_manifest import CustomManifestCreator
    creator = CustomManifestCreator()
    
    success, message = creator.delete_custom_manifest('$selected_manifest')
    
    if success:
        print(f'SUCCESS: {message}')
        exit(0)
    else:
        print(f'ERROR: {message}')
        exit(1)
        
except Exception as e:
    print(f'ERROR: Failed to delete manifest: {e}')
    exit(1)
"
    
    local result
    result=$(python3 -c "$python_script" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
      green_echo "[+] ${result#SUCCESS: }"
    else
      green_echo "[!] ${result#ERROR: }"
    fi
  else
    green_echo "[!] Error: Python3 is required for manifest deletion"
    green_echo "    Install with: sudo apt install python3"
  fi
}

while true; do
  # Show appropriate menu
  if [ -z "$CURRENT_CATEGORY" ]; then
    show_main_menu
  else
    show_menu "$CURRENT_CATEGORY"
  fi
  
  read -rp "Enter your choice: " choice

  # Handle letter commands
  case "$choice" in
    0)
      green_echo "Exiting. Goodbye!"
      break
      ;;
    b|B)
      # Back to main menu
      CURRENT_CATEGORY=""
      SEARCH_FILTER=""
      continue
      ;;
    h|H)
      if [ -z "$CURRENT_CATEGORY" ]; then
        show_help
      else
        green_echo "[!] Invalid choice in this menu. Press 'b' for main menu."
        sleep 1
      fi
      continue
      ;;
    u|U)
      if [ -z "$CURRENT_CATEGORY" ] && [ "$REPO_ENABLED" = true ]; then
        green_echo "[*] Checking for updates..."
        check_for_updates
        green_echo "[+] Update check complete. $REPO_UPDATES_AVAILABLE updates available."
        sleep 2
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
    s|S)
      search_scripts
      continue
      ;;
    e|E)
      if [ "$CURRENT_CATEGORY" = "custom" ]; then
        edit_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
    d|D)
      if [ "$CURRENT_CATEGORY" = "custom" ]; then
        delete_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
      ;;
  esac

  # Handle numeric choices for main menu categories
  if [ -z "$CURRENT_CATEGORY" ]; then
    case "$choice" in
      1)
        CURRENT_CATEGORY="install"
        continue
        ;;
      2)
        CURRENT_CATEGORY="tools"
        continue
        ;;
      3)
        CURRENT_CATEGORY="exercises"
        continue
        ;;
      4)
        CURRENT_CATEGORY="uninstall"
        continue
        ;;
      *)
        # Check if choice matches a dynamic category
        found_dynamic=false
        if [ -n "$DYNAMIC_CATEGORY_MAP" ]; then
          for mapping in $DYNAMIC_CATEGORY_MAP; do
            map_num="${mapping%%:*}"
            map_category="${mapping#*:}"
            if [ "$choice" = "$map_num" ]; then
              CURRENT_CATEGORY="$map_category"
              found_dynamic=true
              break
            fi
          done
        fi
        
        if [ "$found_dynamic" = true ]; then
          continue
        fi
        
        # Check for repository menu
        if [ "$choice" = "$REPO_MENU_NUM" ] && [ "$REPO_ENABLED" = true ]; then
          show_repository_menu
          continue
        fi
        
        # Check for custom manifests menu
        if [ "$choice" = "$MANIFEST_MENU_NUM" ]; then
          show_custom_manifest_menu
          continue
        fi
        
        green_echo "[!] Invalid choice. Select a valid option, or: h (help), s (search), 0 (exit)"
        sleep 2
        continue
        ;;
    esac
  fi

  # Handle numeric choices for script execution
  if [[ ! "$choice" =~ ^[0-9]+$ ]]; then
    green_echo "[!] Invalid choice. Use a number, s (search), b (back), or 0 (exit)"
    sleep 2
    continue
  fi

  # Map display number to actual index if in a category view
  actual_index=""
  if [ -n "$CURRENT_CATEGORY" ] && [ -n "${DISPLAY_TO_INDEX[$choice]}" ]; then
    actual_index=${DISPLAY_TO_INDEX[$choice]}
  else
    actual_index=$((choice-1))
  fi

  if [ -n "${SCRIPTS[$actual_index]}" ]; then
    script="${SCRIPTS[$actual_index]}"
    
    # Skip separator entries
    if [ -z "$script" ]; then
      green_echo "[!] Invalid choice: separators cannot be executed"
      sleep 1
      continue
    fi
    
    run_script "$script" || true
    echo
    green_echo "Press Enter to return to the menu..."
    read -r
  else
    green_echo "[!] Invalid choice: $choice (must be between 1 and ${#SCRIPTS[@]})"
    sleep 2
  fi
done