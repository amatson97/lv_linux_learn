#!/bin/bash
# Description: Extract 7z archives using RAM disk (/dev/shm) for improved performance
# This script will extract all 7z files in a directory utilizing the /dev/shm ram disk.
# Better performance for larger operations, just watch your RAM usage.

# Exit on error
set -e

# Enable extended pattern matching
shopt -s nullglob

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

# Parse command-line arguments
target_dir="${1:-.}"

# Validate and resolve target directory
if [ ! -d "$target_dir" ]; then
  green_echo "[!] Error: Directory does not exist: $target_dir"
  exit 1
fi

# Change to target directory
cd "$target_dir" || exit 1
green_echo "[*] Working directory: $(pwd)"

# Temporary directory in /dev/shm
temp_dir="/dev/shm/extract_temp_$$"

# Create temporary directory
mkdir -p "$temp_dir"
green_echo "[*] Created temp directory: $temp_dir"

# Count archives
archive_count=$(ls -1 *.7z 2>/dev/null | wc -l)

if [ "$archive_count" -eq 0 ]; then
  green_echo "[!] No .7z files found in $(pwd)"
  rmdir "$temp_dir"
  exit 0
fi

green_echo "[*] Found $archive_count .7z archive(s) to process"

# Loop through all .7z files in the target directory
processed=0
failed=0

for archive in *.7z; do
  green_echo "[*] Extracting: $archive"

  # Extract to temporary directory in /dev/shm
  if 7z x "$archive" -o"$temp_dir" >/dev/null; then
    green_echo "[+] Extraction successful. Moving files..."

    # Move extracted files from temp_dir to current directory
    mv "$temp_dir"/* .

    # Remove original archive
    rm -f "$archive"
    
    ((processed++))
    green_echo "[+] Completed: $archive ($processed/$archive_count)"
  else
    green_echo "[!] Extraction failed for: $archive"
    ((failed++))
  fi

  # Clean temp_dir for next archive
  rm -rf "$temp_dir"/*
done

# Remove temporary directory
rmdir "$temp_dir"

green_echo "[+] Processing complete: $processed extracted, $failed failed"