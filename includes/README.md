# Shell Script Includes & Shared Functions

This directory contains reusable shell functions and includes used across the project.

## Contents

### Core Includes
- **main.sh** - Main shared functions and helpers used throughout the project
  - Color output functions (`green_echo`, `red_echo`, etc.)
  - Common utility functions
  - Logging helpers
  - Desktop launcher creation
  - Path management

- **repository.sh** - Repository and script management functions
  - Multi-repository support
  - Cache operations
  - Script downloading and validation
  - Manifest handling
  - Update management

## Purpose

These include files provide:
- **Code reuse** - Common functions used across scripts
- **Consistency** - Standardized patterns across the project
- **Modularity** - Separation of concerns
- **Maintainability** - Centralized helpers for easier updates

## Usage

### Sourcing in Scripts

```bash
#!/bin/bash
set -euo pipefail

# Detect repository root
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

# Source main functions
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Use functions from includes
green_echo "Status message"
```

### Compatible Execution Contexts

These includes work in both contexts:
1. **Local repository execution** - Running scripts from the repo directly
2. **Cached execution** - Running downloaded scripts from cache directory (`~/.lv_linux_learn/script_cache/`)

### Key Functions

**main.sh:**
- `green_echo "message"` - Print green status messages
- `check_package "package_name"` - Check if package is installed
- `create_launcher` - Create desktop launchers

**repository.sh:**
- `fetch_manifest "url"` - Download and parse manifests
- `download_script "url"` - Download script with validation
- `check_for_updates` - Check for cached script updates

## Path Handling

Includes use absolute paths and detect execution context:
- Local: `includes/main.sh`
- Cached: `~/.lv_linux_learn/script_cache/includes/main.sh`

## Related Directories

- **../scripts/** - Installation scripts that use these includes
- **../tools/** - Utility tools
- **../lib/** - Python library (alternative implementations)

## Best Practices

1. Keep functions modular and focused
2. Use meaningful function names
3. Include documentation in function comments
4. Handle errors gracefully with `set -euo pipefail`
5. Use absolute paths in includes
