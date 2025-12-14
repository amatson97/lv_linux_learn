#!/bin/bash
# Description: Batch FLAC to MP3 audio converter with quality control
#
# Converts FLAC lossless audio files to MP3 format using ffmpeg with
# configurable bitrate settings. Preserves metadata and supports batch
# processing of entire directories. Requires ffmpeg to be installed.

# Directory containing FLAC files; default to current directory if not specified
DIR="${1:-.}"

# Bitrate for MP3 encoding (adjustable)
BITRATE="192k"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
  echo "[!] ffmpeg not installed, installing..."
  sudo apt update
  sudo apt install -y ffmpeg
  exit 1
fi

# Convert each .flac file to .mp3 in the same directory
for flac_file in "$DIR"/*.flac; do
  # Check if any .flac files exist
  if [[ ! -e "$flac_file" ]]; then
    echo "No .flac files found in $DIR"
    exit 0
  fi

  mp3_file="${flac_file%.flac}.mp3"
  echo "Converting '$flac_file' to '$mp3_file'..."
  ffmpeg -i "$flac_file" -ab "$BITRATE" -map_metadata 0 -id3v2_version 3 "$mp3_file"
done

echo "Conversion complete."
