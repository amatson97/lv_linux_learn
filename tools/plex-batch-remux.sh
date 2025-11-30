#!/bin/bash
# Batch remux .mkv files (dual audio/soft subs) to MP4 for Plex NVIDIA Quadro M2000 NVENC hardware transcoding [web:34][web:60]
# Ubuntu 24.04: sudo apt install ffmpeg nvidia-driver-550 nvidia-utils-550 [memory:6]
# Quadro M2000 supports NVENC H.264/HEVC transcoding in Plex (Linux driver required) [web:34]
# Nvidia docker tool git required for passing GPU through to docker container.
# Usage: ./plex-batch-remux.sh /path/to/mkv/folder  (creates .mp4 alongside each .mkv)

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <mkv_directory>"
    exit 1
fi

MKV_DIR="$1"
cd "$MKV_DIR" || exit 1

# Process all .mkv files
for input in *.mkv; do
    [[ -f "$input" ]] || { echo "No .mkv files found"; exit 0; }
    
    output="${input%.*}.mp4"
    if [ -f "$output" ]; then
        echo "Skipping (exists): $input -> $output"
        continue
    fi

    echo "Processing: $input"

    # Detect streams
    video=$(ffprobe -v quiet -select_streams v:0 -show_entries stream=index -of csv=p=0 "$input" 2>/dev/null || echo "0")
    audio1=$(ffprobe -v quiet -select_streams a:0 -show_entries stream=index -of csv=p=0 "$input" 2>/dev/null || echo "")
    audio2=$(ffprobe -v quiet -select_streams a:1 -show_entries stream=index -of csv=p=0 "$input" 2>/dev/null || echo "")
    subs=$(ffprobe -v quiet -select_streams s:0 -show_entries stream=index -of csv=p=0 "$input" 2>/dev/null || echo "")

    echo "  Video: $video, Audio: $audio1 $audio2, Subs: $subs"

    # Fast remux: copy compatible streams, convert subs to mov_text (Plex subtitle format)
    # NVENC handles H.264/AAC in MP4 containers perfectly for direct play/stream [web:34][web:60]
    ffmpeg -i "$input" \
        -map 0:v -map 0:a? -map 0:s? \
        -c:v copy -c:a copy -c:s mov_text \
        -movflags +faststart \
        -avoid_negative_ts make_zero \
        "$output" -y
    
    echo "  ✓ Created: $output"
done

echo "Batch complete. Plex NVENC tip: Settings > Transcoder > Use hardware acceleration when available [web:34]"