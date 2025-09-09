#!/bin/bash

# Directory where the 7zip files are located
source_dir="/steam_backup/Roms/Microsoft - XBOX/XBOX HDD ready (#-I) [20140930]"
# Destination directory where the ISO files will be saved
destination_dir="/xboxdrive"

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
    /xboxdrive/extract-xiso/build/./extract-xiso -c ./* "$destination_dir/$filename.iso"
    #./extract-xiso -c ./halo-ce /home/me/games/halo-ce.iso
    #genisoimage -o "$destination_dir/$filename.iso" -R -J ./*
    # Remove the extracted folder
    rm -rf "$destination_dir/$filename"
done

echo "Conversion completed successfully!"
