#!/bin/bash
# Repository management functions for LV Script Manager
# Provides remote script fetching, caching, and update management

# Repository configuration
REPO_URL="https://raw.githubusercontent.com/amatson97/lv_linux_learn/main"
CONFIG_DIR="$HOME/.lv_linux_learn"
CONFIG_FILE="$CONFIG_DIR/config.json"
MANIFEST_FILE="$CONFIG_DIR/manifest.json"
MANIFEST_META_FILE="$CONFIG_DIR/manifest_metadata.json"
SCRIPT_CACHE_DIR="$CONFIG_DIR/script_cache"
REPO_LOG_FILE="$CONFIG_DIR/logs/repository.log"

# Global variables
REPO_ENABLED=true
REPO_UPDATES_AVAILABLE=0
declare -A SCRIPT_VERSIONS
declare -A SCRIPT_IDS
declare -A SCRIPT_STATUS

# ============================================================================
# Configuration Management
# ============================================================================

init_repo_config() {
  # Create directory structure
  mkdir -p "$CONFIG_DIR"/{script_cache,logs}
  mkdir -p "$SCRIPT_CACHE_DIR"/{install,tools,exercises,uninstall}
  
  # Create default config if it doesn't exist
  if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
{
  "version": "1.0.0",
  "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
  "use_remote_scripts": true,
  "fallback_to_bundled": false,
  "auto_check_updates": true,
  "auto_install_updates": true,
  "update_check_interval_minutes": 30,
  "last_update_check": null,
  "allow_insecure_downloads": false,
  "cache_timeout_days": 30,
  "verify_checksums": true
}
EOF
  fi
  
  # Create manifest metadata if it doesn't exist
  if [ ! -f "$MANIFEST_META_FILE" ]; then
    cat > "$MANIFEST_META_FILE" << 'EOF'
{
  "last_fetch": null,
  "manifest_version": null,
  "cached_scripts": []
}
EOF
  fi
}

get_config_value() {
  local key="$1"
  local default="$2"
  
  if [ ! -f "$CONFIG_FILE" ]; then
    echo "$default"
    return 0
  fi
  
  if ! command -v jq &> /dev/null; then
    echo "$default"
    return 0
  fi
  
  local value
  value=$(jq -r ".$key // \"$default\"" "$CONFIG_FILE" 2>/dev/null || echo "$default")
  echo "$value"
}

set_config_value() {
  local key="$1"
  local value="$2"
  
  if ! command -v jq &> /dev/null; then
    return 1
  fi
  
  local temp_file
  temp_file=$(mktemp)
  
  jq --arg key "$key" --arg val "$value" '.[$key] = $val' "$CONFIG_FILE" > "$temp_file" && mv "$temp_file" "$CONFIG_FILE"
}

unset_config_value() {
  local key="$1"
  if [ -z "$key" ]; then
    return 1
  fi
  if [ ! -f "$CONFIG_FILE" ] || ! command -v jq &> /dev/null; then
    return 0
  fi
  local temp_file
  temp_file=$(mktemp)
  jq --arg key "$key" 'del(.[$key])' "$CONFIG_FILE" > "$temp_file" && mv "$temp_file" "$CONFIG_FILE"
}

# ============================================================================
# Logging
# ============================================================================

log_repo_activity() {
  local message="$1"
  local timestamp=$(date -Iseconds)
  
  mkdir -p "$(dirname "$REPO_LOG_FILE")"
  echo "[$timestamp] $message" >> "$REPO_LOG_FILE"
}

# ============================================================================
# Manifest Operations
# ============================================================================

fetch_remote_manifest() {
  local manifest_url="$REPO_URL/manifest.json"
  local temp_manifest
  temp_manifest=$(mktemp)
  
  log_repo_activity "Fetching manifest from $manifest_url"
  
  # Try to download manifest
  if curl -sS -f -m 30 "$manifest_url" -o "$temp_manifest" 2>/dev/null; then
    # Verify it's valid JSON
    if jq empty "$temp_manifest" 2>/dev/null; then
      mv "$temp_manifest" "$MANIFEST_FILE"
      
      # Update metadata
      local timestamp=$(date -Iseconds)
      local version=$(jq -r '.repository_version // "unknown"' "$MANIFEST_FILE")
      
      if command -v jq &> /dev/null; then
        local temp_meta
        temp_meta=$(mktemp)
        jq --arg ts "$timestamp" --arg ver "$version" \
           '.last_fetch = $ts | .manifest_version = $ver' \
           "$MANIFEST_META_FILE" > "$temp_meta" && mv "$temp_meta" "$MANIFEST_META_FILE"
      fi
      
      log_repo_activity "Manifest fetched successfully (version: $version)"
      set_config_value "last_update_check" "$timestamp"
      return 0
    else
      log_repo_activity "ERROR: Invalid JSON in downloaded manifest"
      rm -f "$temp_manifest"
      return 1
    fi
  else
    log_repo_activity "ERROR: Failed to download manifest"
    rm -f "$temp_manifest"
    return 1
  fi
}

load_local_manifest() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    return 1
  fi
  
  if ! jq empty "$MANIFEST_FILE" 2>/dev/null; then
    log_repo_activity "ERROR: Local manifest is corrupted"
    return 1
  fi
  
  return 0
}

get_script_count() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    echo "0"
    return
  fi
  
  jq '.scripts | length' "$MANIFEST_FILE" 2>/dev/null || echo "0"
}

get_script_by_id() {
  local script_id="$1"
  
  if [ ! -f "$MANIFEST_FILE" ]; then
    return 1
  fi
  
  jq -r ".scripts[] | select(.id == \"$script_id\")" "$MANIFEST_FILE" 2>/dev/null
}

get_script_by_filename() {
  local filename="$1"
  
  if [ ! -f "$MANIFEST_FILE" ]; then
    return 1
  fi
  
  jq -r ".scripts[] | select(.file_name == \"$filename\")" "$MANIFEST_FILE" 2>/dev/null
}

get_script_info() {
  local script_id="$1"
  local field="$2"
  
  local script_data
  script_data=$(get_script_by_id "$script_id")
  
  if [ -z "$script_data" ]; then
    return 1
  fi
  
  echo "$script_data" | jq -r ".$field // \"\"" 2>/dev/null
}

# ============================================================================
# Update Checking
# ============================================================================

is_update_check_needed() {
  local last_check=$(get_config_value "last_update_check" "null")
  local interval=$(get_config_value "update_check_interval_minutes" "30")
  
  if [ "$last_check" = "null" ] || [ -z "$last_check" ]; then
    return 0
  fi
  
  # Convert to timestamps and compare
  local last_ts=$(date -d "$last_check" +%s 2>/dev/null || echo "0")
  local now_ts=$(date +%s)
  local diff=$(( (now_ts - last_ts) / 60 ))
  
  if [ "$diff" -ge "$interval" ]; then
    return 0
  fi
  
  return 1
}

check_for_updates() {
  log_repo_activity "Checking for updates..."
  
  # Fetch latest manifest
  if ! fetch_remote_manifest; then
    log_repo_activity "Failed to fetch manifest, using cached version"
    return 1
  fi
  
  # Count available updates
  local update_count=0
  
  if [ ! -f "$MANIFEST_FILE" ]; then
    REPO_UPDATES_AVAILABLE=0
    return 0
  fi
  
  # Get list of cached scripts and check versions
  local script_count=$(get_script_count)
  
  for ((i=0; i<script_count; i++)); do
    local script_id=$(jq -r ".scripts[$i].id" "$MANIFEST_FILE" 2>/dev/null)
    local category=$(jq -r ".scripts[$i].category" "$MANIFEST_FILE" 2>/dev/null)
    local filename=$(jq -r ".scripts[$i].file_name" "$MANIFEST_FILE" 2>/dev/null)
    local remote_checksum=$(jq -r ".scripts[$i].checksum" "$MANIFEST_FILE" 2>/dev/null | cut -d: -f2)
    
    local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
    
    if [ -f "$cached_path" ]; then
      # Compare checksums
      local local_checksum=$(sha256sum "$cached_path" | awk '{print $1}')
      
      if [ "$local_checksum" != "$remote_checksum" ]; then
        update_count=$((update_count + 1))
      fi
    fi
  done
  
  REPO_UPDATES_AVAILABLE=$update_count
  log_repo_activity "Found $update_count updates available"
  
  # Auto-install if enabled
  if [ "$update_count" -gt 0 ]; then
    local auto_install=$(get_config_value "auto_install_updates" "false")
    if [ "$auto_install" = "true" ]; then
      log_repo_activity "Auto-installing updates..."
      update_all_scripts_silent
    fi
  fi
  
  return 0
}

get_update_count() {
  echo "$REPO_UPDATES_AVAILABLE"
}

list_available_updates() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    return 0
  fi
  
  echo "Available Updates:"
  echo
  
  local script_count=$(get_script_count)
  local found_updates=false
  
  for ((i=0; i<script_count; i++)); do
    local script_id=$(jq -r ".scripts[$i].id" "$MANIFEST_FILE" 2>/dev/null)
    local script_name=$(jq -r ".scripts[$i].name" "$MANIFEST_FILE" 2>/dev/null)
    local category=$(jq -r ".scripts[$i].category" "$MANIFEST_FILE" 2>/dev/null)
    local filename=$(jq -r ".scripts[$i].file_name" "$MANIFEST_FILE" 2>/dev/null)
    local version=$(jq -r ".scripts[$i].version" "$MANIFEST_FILE" 2>/dev/null)
    local remote_checksum=$(jq -r ".scripts[$i].checksum" "$MANIFEST_FILE" 2>/dev/null | cut -d: -f2)
    
    local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
    
    if [ -f "$cached_path" ]; then
      local local_checksum=$(sha256sum "$cached_path" | awk '{print $1}')
      
      if [ "$local_checksum" != "$remote_checksum" ]; then
        printf "  • %s (v%s) - %s\n" "$script_name" "$version" "$category"
        found_updates=true
      fi
    fi
  done
  
  if [ "$found_updates" = false ]; then
    echo "  No updates available"
  fi
  
  echo
}

# ============================================================================
# Script Downloading
# ============================================================================

download_script() {
  local script_id="$1"
  
  log_repo_activity "Downloading script: $script_id"
  
  # Get script info from manifest
  local download_url=$(get_script_info "$script_id" "download_url")
  local filename=$(get_script_info "$script_id" "file_name")
  local category=$(get_script_info "$script_id" "category")
  local checksum=$(get_script_info "$script_id" "checksum")
  
  if [ -z "$download_url" ] || [ -z "$filename" ]; then
    log_repo_activity "ERROR: Script not found in manifest: $script_id"
    return 1
  fi
  
  local dest_path="$SCRIPT_CACHE_DIR/$category/$filename"
  local temp_file
  temp_file=$(mktemp)
  
  # Download script
  if curl -sS -f -m 30 "$download_url" -o "$temp_file" 2>/dev/null; then
    # Verify checksum
    if verify_checksum "$temp_file" "$checksum"; then
      mkdir -p "$(dirname "$dest_path")"
      mv "$temp_file" "$dest_path"
      chmod +x "$dest_path"
      log_repo_activity "Downloaded successfully: $dest_path"
      return 0
    else
      log_repo_activity "ERROR: Checksum verification failed for $script_id"
      rm -f "$temp_file"
      return 1
    fi
  else
    log_repo_activity "ERROR: Failed to download $script_id"
    rm -f "$temp_file"
    return 1
  fi
}

verify_checksum() {
  local file="$1"
  local expected_checksum="$2"
  
  # Extract checksum value (remove sha256: prefix if present)
  expected_checksum="${expected_checksum#sha256:}"
  
  local actual_checksum
  actual_checksum=$(sha256sum "$file" | awk '{print $1}')
  
  if [ "$actual_checksum" = "$expected_checksum" ]; then
    return 0
  else
    log_repo_activity "Checksum mismatch: expected $expected_checksum, got $actual_checksum"
    return 1
  fi
}

install_remote_script() {
  local script_id="$1"
  
  download_script "$script_id"
}

update_single_script() {
  local script_id="$1"
  
  log_repo_activity "Updating script: $script_id"
  download_script "$script_id"
}

update_all_scripts() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    green_echo "[!] No manifest available. Run 'Check for Updates' first."
    return 1
  fi
  
  green_echo "[*] Updating all cached scripts..."
  
  local script_count=$(get_script_count)
  local updated=0
  local failed=0
  
  for ((i=0; i<script_count; i++)); do
    local script_id=$(jq -r ".scripts[$i].id" "$MANIFEST_FILE" 2>/dev/null)
    local script_name=$(jq -r ".scripts[$i].name" "$MANIFEST_FILE" 2>/dev/null)
    local category=$(jq -r ".scripts[$i].category" "$MANIFEST_FILE" 2>/dev/null)
    local filename=$(jq -r ".scripts[$i].file_name" "$MANIFEST_FILE" 2>/dev/null)
    
    local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
    
    # Only update if already cached
    if [ -f "$cached_path" ]; then
      green_echo "[*] Updating $script_name..."
      
      if download_script "$script_id"; then
        updated=$((updated + 1))
      else
        failed=$((failed + 1))
      fi
    fi
  done
  
  green_echo "[+] Update complete: $updated updated, $failed failed"
  log_repo_activity "Batch update: $updated updated, $failed failed"
  
  # Recheck for updates
  REPO_UPDATES_AVAILABLE=0
}

update_all_scripts_silent() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    return 1
  fi
  
  log_repo_activity "Silent update of all cached scripts..."
  
  local script_count=$(get_script_count)
  local updated=0
  
  for ((i=0; i<script_count; i++)); do
    local script_id=$(jq -r ".scripts[$i].id" "$MANIFEST_FILE" 2>/dev/null)
    local category=$(jq -r ".scripts[$i].category" "$MANIFEST_FILE" 2>/dev/null)
    local filename=$(jq -r ".scripts[$i].file_name" "$MANIFEST_FILE" 2>/dev/null)
    
    local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
    
    if [ -f "$cached_path" ]; then
      if download_script "$script_id" 2>/dev/null; then
        updated=$((updated + 1))
      fi
    fi
  done
  
  log_repo_activity "Silent update complete: $updated scripts updated"
  REPO_UPDATES_AVAILABLE=0
}

# ============================================================================
# Cache Management
# ============================================================================

get_cached_script_path() {
  local script_id="$1"
  
  local category=$(get_script_info "$script_id" "category")
  local filename=$(get_script_info "$script_id" "file_name")
  
  if [ -z "$category" ] || [ -z "$filename" ]; then
    return 1
  fi
  
  local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
  
  if [ -f "$cached_path" ]; then
    echo "$cached_path"
    return 0
  fi
  
  return 1
}

is_script_cached() {
  local script_id="$1"
  
  local cached_path=$(get_cached_script_path "$script_id" 2>/dev/null)
  
  if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
    return 0
  fi
  
  return 1
}

list_cached_scripts() {
  echo "Cached Scripts:"
  echo
  
  local found=false
  
  for category_dir in "$SCRIPT_CACHE_DIR"/*; do
    if [ -d "$category_dir" ]; then
      local category=$(basename "$category_dir")
      
      for script in "$category_dir"/*.sh; do
        if [ -f "$script" ]; then
          local filename=$(basename "$script")
          local script_data=$(get_script_by_filename "$filename")
          
          if [ -n "$script_data" ]; then
            local name=$(echo "$script_data" | jq -r '.name')
            local version=$(echo "$script_data" | jq -r '.version')
            printf "  • %s (v%s) - %s\n" "$name" "$version" "$category"
            found=true
          fi
        fi
      done
    fi
  done
  
  if [ "$found" = false ]; then
    echo "  No cached scripts"
  fi
  
  echo
}

clear_script_cache() {
  green_echo "[!] This will remove all cached scripts."
  read -rp "Are you sure? [y/N]: " confirm
  
  if [[ "${confirm,,}" == "y" ]]; then
    rm -rf "$SCRIPT_CACHE_DIR"/*
    mkdir -p "$SCRIPT_CACHE_DIR"/{install,tools,exercises,uninstall}
    green_echo "[+] Cache cleared"
    log_repo_activity "Cache cleared by user"
  else
    green_echo "[*] Cancelled"
  fi
}

count_cached_scripts() {
  local count=0
  
  for category_dir in "$SCRIPT_CACHE_DIR"/*; do
    if [ -d "$category_dir" ]; then
      for script in "$category_dir"/*.sh; do
        if [ -f "$script" ]; then
          count=$((count + 1))
        fi
      done
    fi
  done
  
  echo "$count"
}

# ============================================================================
# Script Resolution
# ============================================================================

resolve_script_path() {
  local filename="$1"
  local category="$2"
  
  # Get script ID from filename
  local script_data=$(get_script_by_filename "$filename")
  
  if [ -z "$script_data" ]; then
    # Not in manifest, return empty
    return 1
  fi
  
  local script_id=$(echo "$script_data" | jq -r '.id')
  
  # Priority 1: Cached version
  local cached_path=$(get_cached_script_path "$script_id" 2>/dev/null)
  if [ -n "$cached_path" ] && [ -f "$cached_path" ]; then
    echo "$cached_path"
    return 0
  fi
  
  # No bundled fallback per requirements
  return 1
}

get_script_status() {
  local filename="$1"
  
  local script_data=$(get_script_by_filename "$filename")
  
  if [ -z "$script_data" ]; then
    echo "unknown"
    return
  fi
  
  local script_id=$(echo "$script_data" | jq -r '.id')
  local category=$(echo "$script_data" | jq -r '.category')
  local remote_checksum=$(echo "$script_data" | jq -r '.checksum' | cut -d: -f2)
  
  local cached_path="$SCRIPT_CACHE_DIR/$category/$filename"
  
  if [ -f "$cached_path" ]; then
    local local_checksum=$(sha256sum "$cached_path" | awk '{print $1}')
    
    if [ "$local_checksum" = "$remote_checksum" ]; then
      echo "cached"
    else
      echo "outdated"
    fi
  else
    echo "not_installed"
  fi
}

get_script_version() {
  local filename="$1"
  
  local script_data=$(get_script_by_filename "$filename")
  
  if [ -z "$script_data" ]; then
    echo "unknown"
    return
  fi
  
  echo "$script_data" | jq -r '.version'
}

# ============================================================================
# Utility Functions
# ============================================================================

compare_versions() {
  local v1="$1"
  local v2="$2"
  
  if [ "$v1" = "$v2" ]; then
    echo "0"
    return
  fi
  
  local IFS=.
  local i ver1=($v1) ver2=($v2)
  
  for ((i=0; i<${#ver1[@]} || i<${#ver2[@]}; i++)); do
    if [ "${ver1[i]:-0}" -gt "${ver2[i]:-0}" ]; then
      echo "1"
      return
    elif [ "${ver1[i]:-0}" -lt "${ver2[i]:-0}" ]; then
      echo "-1"
      return
    fi
  done
  
  echo "0"
}

ensure_cache_structure() {
  mkdir -p "$CONFIG_DIR"/{script_cache,logs}
  mkdir -p "$SCRIPT_CACHE_DIR"/{install,tools,exercises,uninstall}
}

# ============================================================================
# Download All Scripts (Initial Setup)
# ============================================================================

download_all_scripts() {
  if [ ! -f "$MANIFEST_FILE" ]; then
    green_echo "[!] Fetching manifest..."
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
    
    green_echo "[*] Downloading $script_name..."
    
    if download_script "$script_id"; then
      downloaded=$((downloaded + 1))
    else
      failed=$((failed + 1))
    fi
  done
  
  green_echo "[+] Download complete: $downloaded downloaded, $failed failed"
  log_repo_activity "Initial download: $downloaded scripts downloaded"
}

# ============================================================================
# Includes Management
# ============================================================================

get_repository_url() {
  # Get repository URL from manifest if available, otherwise use default
  if [ -f "$MANIFEST_FILE" ]; then
    local manifest_repo_url=$(jq -r '.repository_url // empty' "$MANIFEST_FILE" 2>/dev/null)
    if [ -n "$manifest_repo_url" ] && [ "$manifest_repo_url" != "null" ]; then
      echo "$manifest_repo_url"
      return 0
    fi
  fi
  
  # Fallback to config file or default
  if [ -f "$CONFIG_FILE" ]; then
    local config_repo_url=$(jq -r '.repository_url // empty' "$CONFIG_FILE" 2>/dev/null)
    if [ -n "$config_repo_url" ] && [ "$config_repo_url" != "null" ]; then
      echo "$config_repo_url"
      return 0
    fi
  fi
  
  echo "$REPO_URL"
}

ensure_includes_available() {
  local repo_url=$(get_repository_url)
  download_repository_includes "$repo_url"
}

download_repository_includes() {
  local repo_url="$1"
  local includes_cache_dir="$SCRIPT_CACHE_DIR/includes"
  
  # Check if includes are already fresh for this repository
  if are_includes_fresh "$repo_url" "$includes_cache_dir"; then
    return 0
  fi
  
  log_repo_activity "Downloading includes from $repo_url"
  
  # Create includes cache directory
  mkdir -p "$includes_cache_dir"
  
  # Download main.sh (required file)
  local main_url="$repo_url/includes/main.sh"
  local main_file="$includes_cache_dir/main.sh"
  
  if curl -sS -f -m 30 "$main_url" -o "$main_file" 2>/dev/null; then
    chmod 644 "$main_file"
    log_repo_activity "Downloaded main.sh successfully"
  else
    log_repo_activity "ERROR: Failed to download main.sh from $repo_url"
    return 1
  fi
  
  # Try to download repository.sh (optional for some repositories)
  local repo_sh_url="$repo_url/includes/repository.sh"
  local repo_sh_file="$includes_cache_dir/repository.sh"
  
  if curl -sS -f -m 30 "$repo_sh_url" -o "$repo_sh_file" 2>/dev/null; then
    chmod 644 "$repo_sh_file"
    log_repo_activity "Downloaded repository.sh successfully"
  else
    # repository.sh is optional, don't fail on this
    log_repo_activity "NOTE: repository.sh not available (optional)"
  fi
  
  # Mark the includes as fresh for this repository
  mark_includes_fresh "$repo_url" "$includes_cache_dir"
  
  log_repo_activity "Successfully downloaded includes from $repo_url"
  return 0
}

are_includes_fresh() {
  local repo_url="$1"
  local includes_dir="$2"
  
  [ -d "$includes_dir" ] || return 1
  
  local origin_file="$includes_dir/.origin"
  local timestamp_file="$includes_dir/.timestamp"
  
  [ -f "$origin_file" ] && [ -f "$timestamp_file" ] || return 1
  
  # Check if origin matches current repository
  local cached_origin
  cached_origin=$(cat "$origin_file" 2>/dev/null)
  [ "$cached_origin" = "$repo_url" ] || return 1
  
  # Check if timestamp is less than 24 hours old
  local cache_time current_time
  cache_time=$(cat "$timestamp_file" 2>/dev/null)
  current_time=$(date +%s)
  
  # 24 hour cache (86400 seconds)
  [ -n "$cache_time" ] && [ "$((current_time - cache_time))" -lt 86400 ]
}

mark_includes_fresh() {
  local repo_url="$1"
  local includes_dir="$2"
  
  echo "$repo_url" > "$includes_dir/.origin" 2>/dev/null || true
  date +%s > "$includes_dir/.timestamp" 2>/dev/null || true
}
