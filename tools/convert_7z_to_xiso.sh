#!/bin/bash
# Description: Xbox ROM extraction and XISO to ISO conversion utility
#
# Extracts Xbox game ROMs from 7zip archives and converts them from XISO
# format to standard ISO format using extract-xiso binary. Handles batch
# processing of multiple ROM files for Xbox emulation preparation.

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
