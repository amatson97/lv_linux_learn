# Tools & Utilities Guide

Complete guide for utility scripts and bash learning exercises.

## Table of Contents
1. [Utility Tools](#utility-tools)
2. [Bash Learning Exercises](#bash-learning-exercises)
3. [Linux Drive Management](#linux-drive-management)

---

## Utility Tools

The `tools` directory contains various utility scripts for file management and system optimization.

**Common features:**
- Extract 7z and zip files automatically
- Remove source archives after extraction
- Utilize RAM disk for increased performance during operations
- Batch processing capabilities

### Usage

```bash
# Navigate to tools directory
cd tools/

# Make scripts executable
chmod +x *.sh

# Run specific utility (check script comments for usage)
./script_name.sh
```

**Available tools:**
- `7z_extractor*.sh` — Archive extraction with RAM disk support
- `flac_to_mp3.sh` — Audio format conversion
- `convert_*.sh` — Various file format converters
- `check_power_on*.sh` — Check power-on hours of disks
- `extract-xiso/` — Xbox ISO extraction tool

---

## Bash Learning Exercises

The `bash_exercises/` directory contains 8 interactive scripts designed for learning bash fundamentals. Each script features:

- **Professional formatting** with decorative headers and structured output
- **Educational explanations** that describe what concepts are being demonstrated
- **Error handling and validation** for robust execution
- **Interactive pauses** so you can read output before returning to menu
- **Multiple examples** showing different ways to accomplish tasks
- **Real-world usage tips** and command variations

### Available Exercises

1. **hello_world.sh** - Classic first program with script structure explanation
2. **show_date.sh** - Date command with 5+ format examples (ISO 8601, Unix timestamp, 12-hour, etc.)
3. **list_files.sh** - Demonstrates `ls`, `ls -lh`, and `ls -lha` with permission display
4. **make_directory.sh** - Directory creation with input validation and existence checking
5. **print_numbers.sh** - For loops printing 1-10, shows brace expansion, seq, and C-style syntax
6. **simple_calculator.sh** - All 4 basic operations (+, -, ×, ÷) with regex input validation
7. **find_word.sh** - grep searching with file listing, match counting, and line numbers
8. **count_lines.sh** - wc command showing lines, words, characters, and bytes

**Run from the menu or directly:**
```bash
cd bash_exercises/
./hello_world.sh
./show_date.sh
# ... etc
```

Each script sources the shared function library and works seamlessly from both GUI and CLI menus.

---

## Linux Drive Management

Essential resources for disk and storage management:

- [Formatting Disks](https://phoenixnap.com/kb/linux-format-disk)
- [Mounting Disks](https://www.wikihow.com/Linux-How-to-Mount-Drive)
- [Linux Software RAID (mdadm)](https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm)
- [Disable USB Storage Quirk](https://forums.unraid.net/topic/170412-unraid-61210-how-to-permanently-add-a-usb-storage-quirk-to-disable-uas/)
