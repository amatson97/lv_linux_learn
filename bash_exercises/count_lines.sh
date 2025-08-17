#!/bin/bash
# This script prompts the user for a filename, then counts and displays the number of lines in the file.

read -p "Enter filename: " filename
if [[ -f $filename ]]; then
  lines=$(wc -l < "$filename")
  echo "File '$filename' has $lines lines."
else
  echo "File does not exist."
fi
