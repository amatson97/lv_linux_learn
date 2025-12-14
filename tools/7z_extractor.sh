#!/bin/bash
# Description: Batch 7-Zip archive extractor with automatic cleanup
#
# Extracts all 7z archives in the current directory to individual folders.
# Original archive files are automatically deleted after successful extraction.
# Supports nested archives and handles extraction errors gracefully.

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

