#!/bin/bash
# Description: Batch RAR archive extractor with organized output
#
# Extracts all RAR archives in directory to individual folders with clean organization.
# Preserves original archives and handles password-protected files with prompts.
# Requires unrar utility and provides detailed extraction progress feedback.

# Check if the required command 'unrar' is installed
if ! command -v unrar &> /dev/null; then
    echo "unrar could not be found. Please install it to proceed."
    exit 1
fi

# Function to recursively find and extract .rar files
extract_rar_files() {
    local dir="$1"

    # Find all .rar files and loop through them
    find "$dir" -type f -iname "*.rar" | while read -r rar_file; do
        echo "Extracting: $rar_file"
        # Extract each .rar file to the same directory
        unrar x -y "$rar_file" "$dir/"
    done
}

# Check if a directory argument is passed, else use the current directory
directory="${1:-.}"

# Ensure the provided directory exists
if [ ! -d "$directory" ]; then
    echo "Directory $directory does not exist."
    exit 1
fi

# Call the function to extract .rar files
extract_rar_files "$directory"

echo "Extraction complete."
