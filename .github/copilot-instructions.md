# Copilot / AI Agent Instructions — lv_linux_learn

Purpose: Help an AI coding agent be productive in this repo by summarizing architecture, conventions, workflows, and safe constraints discovered in the codebase.

1) Big picture
- This repository is a curated collection of Ubuntu-focused setup and utility scripts (mostly Bash) with multi-repository support. Primary user flows are interactive installers and desktop helpers invoked from `./launcher.sh`, `./menu.sh` (CLI), or `./menu.py` (GUI).
- **Version 2.3.0**: Multi-repository system supporting custom script libraries, remote includes, cache-first execution, and dual CLI/GUI interfaces with feature parity.
- Key responsibilities: install packages (`apt`), configure VPN/networking tools, create desktop launchers, provide utility tools, and manage custom script repositories with automated distribution and caching.

2) Entry points & important paths
- **Primary interfaces**: `./launcher.sh` (auto-detects GUI vs CLI), `./menu.sh` (bash CLI), or `./menu.py` (Python GUI)
- **Repository backends**: `includes/repository.sh` (bash), `lib/repository.py` (Python) — core multi-repository functionality
- **Library modules**: `lib/custom_scripts.py` (CustomScriptManager), `lib/custom_manifest.py` (manifest creation)
- **Shared functions**: `includes/main.sh` — global helpers sourced by scripts, works with both local and cached execution
- **Main directories**: `scripts/`, `tools/`, `zerotier_tools/`, `docker-compose/`, `ai_fun/`, `bash_exercises/`, `uninstallers/`
- **Cache system**: `~/.lv_linux_learn/script_cache/` — downloaded scripts with includes support
- **Configuration**: `~/.lv_linux_learn/config.json` — repository settings including custom manifest URLs
- **Documentation**: Comprehensive docs in `docs/` with README.md kept <250 lines
- **Custom scripts**: Local custom scripts in `~/.lv_linux_learn/custom_scripts.json`, repository scripts via manifest system

3) Coding & style conventions (project-specific)
- **Shell flavor**: scripts use `#!/bin/bash` or `#!/usr/bin/env bash`. Use bash-compatible constructs (arrays, `[[ ... ]]`) rather than strict POSIX `sh`
- **Strict mode**: All new scripts start with `set -euo pipefail` for safety (see section 17 for compatibility notes)
- **Logging**: use `green_echo` helper for status messages. Available in both local and cached execution contexts
- **Shared helpers**: put reusable functions in `includes/main.sh`. Repository-compatible scripts should handle both local and cached includes paths:
  ```bash
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "$script_dir/.." && pwd)"
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
  ```
  See [docker_install.sh](scripts/docker_install.sh) for the preferred pattern
- **Execution contexts**: Scripts must work in both local repository and cached execution (`~/.lv_linux_learn/script_cache/`)
- **Path handling**: Use absolute paths and detect execution context. Cached scripts run from cache directory with symlinked/downloaded includes
- **Desktop integration**: launchers created under `$HOME/.lv_connect` and `$HOME/Desktop` with `gio set <file> metadata::trusted true`
- **Script metadata**: Include description comment at top: `# Description: Brief summary`

4) Safety, secrets & sensitive state
- There are hard-coded tokens/IDs in scripts (example: `NORDVPN_TOKEN` in `includes/main.sh`). Do NOT expose, modify, or commit secrets. If a change requires a token, prompt the repo owner or add configuration to read it from environment variables instead.
- Network identifiers (ZeroTier network IDs) may appear in legacy cleanup scripts. User-configured networks are the standard approach.

5) Developer workflows & testing
- **Quick local test**: Make scripts executable and test both interfaces:
  ```bash
  chmod +x scripts/*.sh includes/*.sh *.sh
  ./menu.sh  # CLI interface
  ./menu.py  # GUI interface (if desktop available)
  # Copilot / AI Agent Instructions — lv_linux_learn

  Purpose: quick, actionable guidance to help an AI coding agent be productive in this multi-repo script manager.

  - Big picture: this repo is a collection of Ubuntu-focused installers/utilities (mostly Bash) with a cache-first multi-repository system and both CLI (`menu.sh`) and GTK GUI (`menu.py`) frontends. Key goals: install packages, manage remote script manifests, and create desktop launchers.

  - Primary entry points: `./launcher.sh` (auto GUI/CLI), `./menu.sh` (CLI), `./menu.py` (GUI). Core backends: `includes/repository.sh` (bash) and `lib/repository.py` (python).

  - Important paths and files:
    - Cache: `~/.lv_linux_learn/script_cache/`
    - Config: `~/.lv_linux_learn/config.json`
    - Manifest tooling: `./dev_tools/update_manifest.sh` (regenerates `manifest.json` with SHA256 checksums)
    - Shared helpers: `includes/main.sh` (sourcing pattern shown below)

  - Sourcing pattern (use in new scripts):
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    repo_root="$(cd "$script_dir/.." && pwd)"
    # shellcheck source=/dev/null
    source "$repo_root/includes/main.sh"

  - Conventions to follow:
    - Use bash (`#!/usr/bin/env bash`), and add `set -euo pipefail` in new scripts.
    - Use `green_echo` for status messages from `includes/main.sh`.
    - Scripts must work both in-repo and when run from the cache directory—detect execution context and prefer absolute paths.
    - GUI dialogs assume GNOME tools (`zenity`, `gsettings`) where used.

  - Common workflows (commands you may run or automate):
    - Run CLI menu: `./menu.sh`
    - Run GUI (desktop): `./menu.py` (requires GTK environment)
    - Regenerate manifest after script changes: `./dev_tools/update_manifest.sh`

  - Safety & secrets: do not expose or commit tokens or network IDs. Several scripts reference tokens (example: `NORDVPN_TOKEN` in `includes/main.sh`)—read from env or config, or ask repo owner before changing.

  - Testing notes: there are no automated unit tests. Validate changes manually in both local and cached contexts. To test cache behavior, run `menu.sh` and exercise repository download/update flows.

  - Key files to consult when implementing or debugging:
    - [includes/main.sh](includes/main.sh) — shared helpers and launcher patterns
    - [includes/repository.sh](includes/repository.sh) — bash repo/cache logic
    - [lib/repository.py](lib/repository.py) and [lib/custom_scripts.py](lib/custom_scripts.py) — GUI/backend equivalents
    - [menu.sh](menu.sh) and [menu.py](menu.py) — entry points; `menu.py` is large and organized into clear sections for manifest loading, UI, and cache ops

  - When in doubt: prefer minimal, backwards-compatible changes; run `./dev_tools/update_manifest.sh` and test `./menu.sh` locally. Ask the repo owner before modifying network or token-related code.

  If you'd like, I can: regenerate the manifest, run a quick static check for `set -euo pipefail` usage, or open a PR with the updated guidance. What should I do next?

