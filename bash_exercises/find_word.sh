#!/bin/bash
# This script prompts for a filename and a word, then shows all lines in the file containing that word (case insensitive).

read -p "Enter filename: " filename
if [[ -f $filename ]]; then
  read -p "Enter word to search: " word
  grep -in "$word" "$filename"
else
  echo "File not found."
fi
