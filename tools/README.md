# Tools - Utility Scripts

This directory contains utility scripts for common system administration and file management tasks.

## Contents

### File Extraction & Conversion
- **7z_extractor.sh** - Extract 7-Zip archives
- **7z_extractor_ram_disk.sh** - Extract to RAM disk for performance
- **extract_rar.sh** - Extract RAR archives
- **zip_extractor_ram_disk.sh** - Extract ZIP to RAM disk
- **convert_7z_to_xiso.sh** - Convert 7Z to XISO format

### Media Tools
- **flac_to_mp3.sh** - Convert FLAC audio to MP3 format
- **plex-batch-remux.sh** - Batch remux videos for Plex media server

### Power Management
- **check_power_on_hours.sh** - Check device power-on hours (useful for HDD/SSD health)

### Git Utilities
- **git_pull.sh** - Pull latest changes from repository
- **git_push_changes.sh** - Push changes to repository

### Network Utilities
- **ubuntu_NetworkManager.sh** - Ubuntu NetworkManager configuration and management

### Subdirectories
- **extract-xiso/** - XISO extraction utilities

## Purpose

These scripts provide:
- **File management** - Extract and convert common file formats
- **Media processing** - Audio/video conversion and optimization
- **System monitoring** - Check hardware status
- **Version control** - Git operations
- **Network management** - Network configuration utilities

## Usage

### Running a Tool

```bash
chmod +x tool_name.sh
./tool_name.sh [options]
```

### Examples

Extract a 7-Zip file:
```bash
./7z_extractor.sh archive.7z /path/to/extract
```

Convert FLAC to MP3:
```bash
./flac_to_mp3.sh input.flac output.mp3
```

Check hard drive power-on hours:
```bash
./check_power_on_hours.sh
```

## Level

🟡 **Intermediate** - System administration and file management

## Dependencies

Most scripts require standard utilities:
- 7z (p7zip)
- unrar
- ffmpeg (for audio conversion)
- git
- smartctl (for power-on hours)

Install dependencies:
```bash
sudo apt install p7zip-full unrar ffmpeg git smartmontools
```

## Related Directories

- **../scripts/** - Installation scripts
- **../bash_exercises/** - Learning resources
- **../includes/** - Shared shell functions

## Status

✅ Production Ready - All scripts tested and documented
