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

# Custom scripts configuration
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

# Dynamic arrays loaded from manifest
declare -a SCRIPTS=()
declare -a DESCRIPTIONS=()
declare -a MENU_SCRIPT_IDS=()

# Ensure cache directory exists
mkdir -p "$CUSTOM_SCRIPTS_DIR"

# Download manifest from configured URL if not cached or older than 1 hour
fetch_manifest() {
  local cache_age=0
  
  # Update MANIFEST_URL if custom URL is set
  if [ -n "${CUSTOM_MANIFEST_URL:-}" ]; then
    MANIFEST_URL="$CUSTOM_MANIFEST_URL"
  fi
  
  if [ -f "$MANIFEST_CACHE" ]; then
    cache_age=$(( $(date +%s) - $(stat -c %Y "$MANIFEST_CACHE" 2>/dev/null || echo 0) ))
  fi
  
  # Fetch if cache doesn't exist or is older than 1 hour (3600 seconds)
  if [ ! -f "$MANIFEST_CACHE" ] || [ $cache_age -gt 3600 ]; then
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
  repo_version=$(jq -r '.repository_version // "unknown"' "$manifest_path" 2>/dev/null)
  last_updated=$(jq -r '.last_updated // "unknown"' "$manifest_path" 2>/dev/null)
  total_scripts=$(jq '.scripts | length' "$manifest_path" 2>/dev/null || echo 0)
  
  green_echo "[*] Loaded manifest version $manifest_version (repo: $repo_version)"
  green_echo "[*] Last updated: $last_updated"
  green_echo "[*] Processing $total_scripts scripts..."
  
  # Clear arrays
  SCRIPTS=()
  DESCRIPTIONS=()
  MENU_SCRIPT_IDS=()
  
  # Track scripts per category
  local install_count=0 tools_count=0 exercises_count=0 uninstall_count=0
  
  # Load each category in order: install, tools, exercises, uninstall
  local categories=("install" "tools" "exercises" "uninstall")
  
  for category in "${categories[@]}"; do
    # Get scripts for this category
    local category_scripts
    category_scripts=$(jq -r ".scripts[] | select(.category == \"$category\") | .relative_path" "$manifest_path" 2>/dev/null)
    
    if [ -n "$category_scripts" ]; then
      local count=0
      # Add scripts from this category
      while IFS= read -r script_path; do
        SCRIPTS+=("$script_path")
        
        # Get description and ID for this script
        local desc script_id
        desc=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .description" "$manifest_path" 2>/dev/null)
        script_id=$(jq -r ".scripts[] | select(.relative_path == \"$script_path\") | .id" "$manifest_path" 2>/dev/null)
        
        DESCRIPTIONS+=("$desc")
        MENU_SCRIPT_IDS+=("$script_id")
        count=$((count + 1))
      done <<< "$category_scripts"
      
      # Update category counters
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
  done
  
  # Display category breakdown
  green_echo "[*] Script breakdown:"
  [ $install_count -gt 0 ] && green_echo "    Install: $install_count scripts"
  [ $tools_count -gt 0 ] && green_echo "    Tools: $tools_count scripts"
  [ $exercises_count -gt 0 ] && green_echo "    Exercises: $exercises_count scripts"
  [ $uninstall_count -gt 0 ] && green_echo "    Uninstall: $uninstall_count scripts"
  
  return 0
}

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

# Then append custom scripts
load_custom_scripts

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
  
  for category in "${categories[@]}"; do
    local category_dir="$cache_dir/$category"
    if [ -d "$category_dir" ]; then
      local count=$(find "$category_dir" -name "*.sh" | wc -l)
      if [ "$count" -gt 0 ]; then
        echo "  📦 $category ($count scripts):"
        find "$category_dir" -name "*.sh" -exec basename {} \; | sort | sed 's/^/    /'
        total_cached=$((total_cached + count))
        echo
      fi
    fi
  done
  
  if [ "$total_cached" -eq 0 ]; then
    echo "  No scripts currently cached."
    echo "  Use 'Download All Scripts' option to populate the cache."
  else
    echo "  Total cached scripts: $total_cached"
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
    
    echo "  Current Settings:"
    echo "  1) Use Remote Scripts:      $use_remote"
    echo "  2) Auto-check Updates:      $auto_check"
    echo "  3) Auto-install Updates:    $auto_install"
    echo "  4) Check Interval:          $interval minutes"
    echo "  5) Verify Checksums:        $verify_checksums"
    echo "  6) Manifest URL:            $current_manifest_url"
    echo
    echo "  Options:"
    echo "   r) Toggle remote scripts"
    echo "   c) Toggle auto-check updates"
    echo "   i) Toggle auto-install updates"
    echo "   t) Change check interval"
    echo "   s) Toggle checksum verification"
    echo "   m) Change manifest URL"
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
      m|M)
        echo
        echo "Current manifest URL: $MANIFEST_URL"
        echo
        read -rp "Enter new manifest URL (or press Enter to reset to default): " new_manifest_url
        
        if [ -z "$new_manifest_url" ]; then
          # Reset to default
          unset CUSTOM_MANIFEST_URL
          MANIFEST_URL="$DEFAULT_MANIFEST_URL"
          # Remove from config if it exists
          if command -v set_config_value &> /dev/null; then
            set_config_value "custom_manifest_url" ""
          fi
          green_echo "[*] Manifest URL reset to default: $MANIFEST_URL"
          green_echo "[*] Clearing manifest cache to force reload..."
          rm -f "$MANIFEST_CACHE" 2>/dev/null || true
          green_echo "[*] Reloading scripts from default repository..."
          load_scripts_from_manifest
          green_echo "[*] Refreshing script counts for main menu..."
          refresh_script_counts
          green_echo "[+] Repository reset to default successfully!"
        else
          # Validate URL format
          if [[ "$new_manifest_url" =~ ^https?:// ]]; then
            export CUSTOM_MANIFEST_URL="$new_manifest_url"
            MANIFEST_URL="$new_manifest_url"
            # Save to config if possible
            if command -v set_config_value &> /dev/null; then
              set_config_value "custom_manifest_url" "$new_manifest_url"
            fi
            green_echo "[*] Manifest URL updated to: $MANIFEST_URL"
            echo
            green_echo "[*] Clearing manifest cache to force reload..."
            rm -f "$MANIFEST_CACHE" 2>/dev/null || true
            green_echo "[*] Reloading scripts from new repository..."
            load_scripts_from_manifest
            green_echo "[*] Refreshing script counts for main menu..."
            refresh_script_counts
            green_echo "[+] Repository switched successfully!"
          else
            green_echo "[!] Invalid URL format. Please use http:// or https://"
          fi
        fi
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
  
  # Use cached script counts or calculate fresh ones
  local install_count="${CACHED_INSTALL_COUNT:-0}"
  local tools_count="${CACHED_TOOLS_COUNT:-0}" 
  local exercises_count="${CACHED_EXERCISES_COUNT:-0}"
  local uninstall_count="${CACHED_UNINSTALL_COUNT:-0}"
  local custom_count
  
  # If cached counts are not available, calculate fresh
  if [ "$install_count" -eq 0 ] && [ "$tools_count" -eq 0 ] && [ "$exercises_count" -eq 0 ] && [ "$uninstall_count" -eq 0 ]; then
    if [ -f "$MANIFEST_CACHE" ] && command -v jq &> /dev/null; then
      install_count=$(jq -r '[.scripts[] | select(.category == "install")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
      tools_count=$(jq -r '[.scripts[] | select(.category == "tools")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0") 
      exercises_count=$(jq -r '[.scripts[] | select(.category == "exercises")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
      uninstall_count=$(jq -r '[.scripts[] | select(.category == "uninstall")] | length' "$MANIFEST_CACHE" 2>/dev/null || echo "0")
    fi
  fi
  
  custom_count=$(jq '.scripts | length' "$CUSTOM_SCRIPTS_JSON" 2>/dev/null || echo "0")
  
  echo "  Select a category:"
  echo
  printf "   \033[1;32m1)\033[0m 📦 Install Scripts         (%d scripts)\n" "$install_count"
  echo "      System tools, browsers, development environments"
  echo
  printf "   \033[1;32m2)\033[0m 🔧 Tools & Utilities       (%d scripts)\n" "$tools_count"
  echo "      File management, git helpers, conversion tools"
  echo
  printf "   \033[1;32m3)\033[0m 📚 Bash Exercises          (%d exercises)\n" "$exercises_count"
  echo "      Learn bash scripting with interactive examples"
  echo
  printf "   \033[1;32m4)\033[0m ⚠️  Uninstall               (%d scripts)\n" "$uninstall_count"
  echo "      Remove installed applications and clean configurations"
  echo
  if [ "$custom_count" -gt 0 ]; then
    printf "   \033[1;32m5)\033[0m 📝 Custom Scripts          (%d scripts)\n" "$custom_count"
    echo "      Your personally added scripts"
    echo
  fi
  
  # Show repository option if enabled
  if [ "$REPO_ENABLED" = true ]; then
    local repo_status="enabled"
    if [ "$REPO_UPDATES_AVAILABLE" -gt 0 ]; then
      repo_status="$REPO_UPDATES_AVAILABLE updates available"
    fi
    printf "   \033[1;32m6)\033[0m 📦 Script Repository       (%s)\n" "$repo_status"
    echo "      Download and update scripts from remote repository"
    echo
  fi
  
  echo "  ────────────────────────────────────────────────────────────────────────────"
  echo "   a) Add Custom Script    h) Help/About    s) Search All    u) Check Updates    0) Exit"
  echo
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
    
    # Compact format: number, name, status on one line
    if [ ! -f "$script" ]; then
      printf "  \033[1;31m%2d)\033[0m %-35s \033[1;31m[MISSING]\033[0m" "$show_num" "$script_name"
      printf "%b\n" "$cache_status"
    elif [ ! -x "$script" ]; then
      printf "  \033[1;33m%2d)\033[0m %-35s \033[1;33m[NOT EXEC]\033[0m" "$show_num" "$script_name"
      printf "%b\n" "$cache_status"
    else
      printf "  \033[1;32m%2d)\033[0m %-35s" "$show_num" "$script_name"
      printf "%b\n" "$cache_status"
    fi
    # Description indented on next line
    printf "      \033[2m%s\033[0m\n" "$desc"
  done
  
  if [ -n "$SEARCH_FILTER" ] && [ "$display_count" -eq 0 ]; then
    echo "  No scripts match your search filter."
  fi
  
  echo
  echo "  ────────────────────────────────────────────────────────────────────────────"
  if [ -n "$category" ]; then
    if [ "$category" = "custom" ]; then
      echo "   e) Edit Script    d) Delete Script    b) Back    s) Search    0) Exit"
    else
      echo "   b) Back to Main Menu    s) Search    0) Exit"
    fi
  else
    echo "   a) Add Custom Script    h) Help/About    s) Search    0) Exit"
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
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
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
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
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
  green_echo "[*] Reloading custom scripts..."
  reload_custom_scripts
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
    echo "  Options:"
    printf "   \033[1;32m1)\033[0m Update All Scripts         ($updates updates)\n"
    echo "   2) Download All Scripts        (bulk download)"
    echo "   3) View Cached Scripts         (list local cache)"
    echo "   4) Clear Script Cache          (remove all cached)"
    echo "   5) Check for Updates           (manual refresh)"
    echo "   6) Repository Settings"
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
        clear
        list_cached_scripts
        read -rp "Press Enter to continue..."
        ;;
      4)
        clear_script_cache
        read -rp "Press Enter to continue..."
        ;;
      5)
        green_echo "[*] Checking for updates..."
        check_for_updates
        green_echo "[+] Update check complete. $REPO_UPDATES_AVAILABLE updates available."
        read -rp "Press Enter to continue..."
        ;;
      6)
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
    a|A)
      if [ -z "$CURRENT_CATEGORY" ]; then
        add_custom_script
      else
        green_echo "[!] Invalid choice in this menu"
        sleep 1
      fi
      continue
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
      5)
        CURRENT_CATEGORY="custom"
        continue
        ;;
      6)
        if [ "$REPO_ENABLED" = true ]; then
          show_repository_menu
        else
          green_echo "[!] Invalid choice"
          sleep 1
        fi
        continue
        ;;
      *)
        green_echo "[!] Invalid choice. Select 1-5, or: a (add), h (help), s (search), 0 (exit)"
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