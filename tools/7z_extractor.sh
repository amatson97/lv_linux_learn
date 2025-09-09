#!/bin/bash
# This script will extract all 7z files in a directory and remove the original archive.

# Exit on error
set -e

# Enable extended pattern matching
shopt -s nullglob

# Loop through all .7z files in the current directory
for archive in *.7z; do
    echo "Extracting: $archive"

    # Extract to current directory
    7z x "$archive"

    if [ $? -eq 0 ]; then
        echo "Extraction successful. Removing $archive"
        rm -f "$archive"
    else
        echo "Extraction failed for $archive"
    fi
done

echo "All .7z files processed."

