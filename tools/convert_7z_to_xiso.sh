#!/bin/bash
# This script was prepared for extract xbox roms from 7zip then converting them from xiso to iso format
# This uses the extract-xiso binary.

# Directory where the 7zip files are located
source_dir="<YOUR SOURCE DIRECTORY>"
# Destination directory where the ISO files will be saved
destination_dir="<YOUR DEST DRIVE>"

# Check if destination directory exists, otherwise create it
if [[ ! -d "$destination_dir" ]]; then
    mkdir -p "$destination_dir"
fi

# Loop through all 7zip files in the source directory
for file in "$source_dir"/*.7z; do

    # Extract the file name without extension
    filename=$(basename "$file" .7z)

    # Convert 7zip file to ISO using p7zip package (make sure it is installed)
    7z x "$file" -o"$destination_dir/$filename"

    # Create an ISO file from the extracted content using /xboxdrive/extract-xiso/build/./extract-xiso 
    cd "$destination_dir/$filename"
    /extract-xiso/build/./extract-xiso -c ./* "$destination_dir/$filename.iso"
    rm -rf "$destination_dir/$filename"
done

echo "Conversion completed successfully!"
