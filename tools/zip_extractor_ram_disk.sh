#!/bin/bash
# This script will extract all zip files in a directory utalising /dev/shm RAM disk.
# orginal archive will be deleted upon completion.
# Keep an eye on RAM usage when using this.

# Exit on error
set -e

# Enable extended pattern matching
shopt -s nullglob

# Temporary directory in /dev/shm
temp_dir="/dev/shm/extract_temp_$$"

# Create temporary directory
mkdir -p "$temp_dir"

# Loop through all .zip files in the current directory
for archive in *.zip; do
  echo "Extracting: $archive"

  # Extract to temporary directory in /dev/shm
  unzip -q "$archive" -d "$temp_dir"

  if [ $? -eq 0 ]; then
    echo "Extraction successful. Moving extracted files to current directory."

    # Move extracted files from temp_dir to current directory
    mv "$temp_dir"/* .

    # Remove original archive
    rm -f "$archive"
  else
    echo "Extraction failed for $archive"
  fi

  # Clean temp_dir for next archive
  rm -rf "$temp_dir"/*
done

# Remove temporary directory
rmdir "$temp_dir"

echo "All .zip files processed."