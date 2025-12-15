# Copilot / AI Agent Instructions — lv_linux_learn

Purpose: Help an AI coding agent be productive in this repo by summarizing architecture, conventions, workflows, and safe constraints discovered in the codebase.

1) Big picture
- This repository is a curated collection of Ubuntu-focused setup and utility scripts (mostly Bash) with multi-repository support. Primary user flows are interactive installers and desktop helpers invoked from `./launcher.sh`, `./menu.sh` (CLI), or `./menu.py` (GUI).
- **Version 2.1.1**: Multi-repository system supporting custom script libraries, remote includes, cache-first execution, and dual CLI/GUI interfaces with feature parity.
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
  ```
- **Manifest generation**: After adding/modifying scripts, regenerate manifest:
  ```bash
  ./dev_tools/update_manifest.sh  # Updates manifest.json with checksums
  ```
  This is critical for repository distribution - manifest includes SHA256 checksums for all scripts
- **Repository system testing**: Test both local and cached execution:
  ```bash
  # Test repository menu (CLI)
  ./menu.sh << 'EOF'
  6
  6
  b
  0
  EOF
  
  # Test cache-first execution by running uncached script
  # Verify includes path resolution in cached context
  ```
- **Multi-repository testing**: Configure custom repositories and test includes download:
  ```bash
  # Set custom manifest URL via environment variable
  export CUSTOM_MANIFEST_URL="https://your-repo/manifest.json"
  ./menu.sh  # Test with custom repository
  ```
- **Individual scripts**: Test in both contexts: `./scripts/foo.sh` and from cache directory
- **Validation**: Manual testing on Ubuntu Desktop VM (24.04.3 LTS recommended)
- **No automated tests**: Rely on manual validation and community testing

6) Dependency & install patterns
- Package manager: `apt` is used across scripts. When adding a new external dependency, update `README.md` with install steps and note any required `sudo` or group membership changes (docker, nordvpn, etc.).
- GUI dialogs: scripts use `zenity` and GNOME `gsettings` — assume GNOME desktop environment unless updating otherwise.

7) Examples & patterns to follow
- Add a new shared helper (style):

  ```bash
  my_helper() {
    green_echo "[*] Doing X..."
    # do work
  }
  ```

- Create trusted desktop launcher (pattern used in `includes/main.sh`): create script under `$HOME/.lv_connect`, make it executable, create a `.desktop` file under `$HOME/Desktop`, then `gio set` the trust flag.

8) Git / commit guidance
- Keep commits small and focused. Test scripts locally before committing. Never commit secrets or tokens; prefer reading them from environment variables or prompting the user.

9) When to ask the repo owner
- Before changing network IDs, hard-coded tokens, or any scripts that modify system networking or user groups (reboots are triggered in some installers).

10) Files to consult when uncertain
- `README.md` — project overview and quick start (streamlined, <250 lines).
- `VERSION` — current version (2.1.1), update when releasing new versions
- `manifest.json` — auto-generated script registry, do not edit manually (use dev_tools/update_manifest.sh)
- `docs/` — detailed topic-specific guides (INSTALLATION.md, DOCKER.md, TROUBLESHOOTING.md, NETWORKING.md, TOOLS.md, AI_TOOLS.md, ADVANCED.md).
- `includes/main.sh` — shared helpers and conventions.
- `includes/repository.sh` — bash repository backend (816 lines, core multi-repo logic)
- `lib/repository.py` — Python repository backend (738 lines, GUI equivalent)
- `lib/custom_scripts.py` — CustomScriptManager for user-added scripts
- `menu.sh`, `menu.py` — entry points and menu system architecture. menu.py uses modular structure with clear section markers.
- `scripts/`, `tools/`, `ai_fun/`, `uninstallers/` — examples of patterns and how installers/uninstallers are implemented.
- `dev_tools/` — manifest generation and maintenance scripts.

10.1) menu.py structure (for AI navigation)
The GUI application (menu.py ~5500 lines) is organized with clear section markers:
- **CONFIGURATION & CONSTANTS** — Package requirements, manifest URLs
- **MANIFEST LOADING FUNCTIONS** — fetch_manifest(), load_scripts_from_manifest()
- **GTK THEME / CSS STYLING** — Application theming
- **MAIN APPLICATION CLASS** — ScriptMenuGTK(Gtk.ApplicationWindow)
  - **CENTRALIZED SCRIPT HANDLING METHODS** — Cache checking, metadata building, execution logic
  - **TAB CREATION & UI BUILDING** — _create_script_tab(), tab switching
  - **PACKAGE MANAGEMENT** — check_required_packages(), install prompts
  - **REPOSITORY TAB & MANAGEMENT** — Repository browser, manifest management
  - **REPOSITORY SELECTION & BULK OPERATIONS** — Download/remove selected scripts
  - **INCLUDES & CACHE MANAGEMENT** — Remote includes, symlink management
  - **PACKAGE INSTALLATION HELPERS** — Terminal-based package installation
  - **EVENT HANDLERS - USER INTERACTIONS** — Button clicks, selection changes
  - **SCRIPT CACHE OPERATIONS** — Download, update, remove scripts
  - **MENU BAR & DIALOGS** — Application menus, about dialog
- **APPLICATION INITIALIZATION** — on_activate(), main()

11) Multi-repository system architecture (v2.1.1)
- **Multi-repository support**: Default GitHub manifest + custom repository configuration via `custom_manifest_url`
- **Remote includes**: Automatic download of includes directories from repository_url in manifest
- **Cache-first execution**: Scripts download to `~/.lv_linux_learn/script_cache/` before execution with user permission
- **Dynamic loading**: Scripts loaded from manifest (local or remote) with category organization
- **Navigation**: 6 main categories (Install, Tools, Exercises, Uninstall, Custom Scripts, Repository)
- **Feature parity**: Identical functionality in CLI (`menu.sh`) and GUI (`menu.py`)
- **Repository menu**: Full repository management (update, download, clear cache, settings)
- **Custom manifest support**: Environment variable `CUSTOM_MANIFEST_URL` or config setting
- **Includes management**: Smart includes resolution for both local and remote repositories

12) Multi-repository architecture (v2.1.1)
- **Default manifest**: https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json
- **Custom repositories**: User-configurable via `custom_manifest_url` in config or `CUSTOM_MANIFEST_URL` env var
- **Local cache**: `~/.lv_linux_learn/script_cache/` with downloaded scripts and includes
- **Repository detection**: Automatic repository_url extraction from manifest for includes download
- **Both interfaces**: CLI and GUI have identical multi-repository capabilities
- **Key backend functions**:
  - `fetch_manifest()` / `parse_manifest()` - Download from configured repository
  - `ensure_remote_includes()` / `_ensure_remote_includes()` - Download remote includes with 24h caching
  - `download_script()` / `download_script()` - Cache script with checksum validation
  - `get_cached_script_path()` - Resolve cached script locations
  - Cache management (clear, update, bulk operations)
- **Custom scripts**: Both local (`custom_scripts.json`) and repository-based scripts supported
- **Visual indicators**: 📝 for custom scripts, cache status for repository scripts

13) Documentation strategy (v2.1.1)
- **Main README.md**: Keep <250 lines, highlight multi-repository system, link to detailed guides
- **Core documentation**: 
  - `docs/SCRIPT_REPOSITORY.md` - Multi-repository system comprehensive guide
  - `docs/CUSTOM_SCRIPTS.md` - Local and repository-based custom scripts
  - `docs/ADVANCED.md` - Multi-repository development and enterprise patterns
  - `docs/REPOSITORY_SECURITY.md` - Security considerations for multi-repository usage
  - `docs/INSTALLATION.md` - Updated with repository configuration guidance
- **Feature documentation**: Multi-repository features documented across multiple files
- **Version consistency**: All documentation reflects v2.1.1 multi-repository capabilities
- **AI guidance**: This copilot-instructions.md provides comprehensive development context
- **Update pattern**: When modifying repository features, update README.md + relevant docs/ files

14) Multi-repository development patterns
- **Creating custom repositories**: Use repository_url field in manifest.json to specify includes base URL
- **Manifest format**: Include repository_url, proper checksums, and category organization
  ```json
  {
    "version": "1.0.0",
    "repository_version": "2.1.1",
    "repository_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main",
    "scripts": [{
      "id": "unique-id",
      "name": "Display Name",
      "category": "install|tools|exercises|uninstall",
      "file_name": "script.sh",
      "relative_path": "scripts/script.sh",
      "download_url": "https://full-url/script.sh",
      "checksum": "sha256:...",
      "description": "Brief summary",
      "requires_sudo": true,
      "dependencies": ["includes-main"]
    }]
  }
  ```
- **Manifest generation**: Use `./dev_tools/update_manifest.sh` to auto-generate checksums and metadata
- **Remote includes**: Custom repositories should provide includes/main.sh with shared functions
- **Security considerations**: All repository URLs must use HTTPS, implement checksum validation
- **Testing custom repositories**: Test with both local and lv_linux_learn system integration
- **Repository configuration**: Support both environment variables and config file settings

15) Cache system integration
- **Cache directory**: `~/.lv_linux_learn/script_cache/` organized by category with includes/ subdirectory
- **Cache-first execution**: Always prefer cached scripts with proper includes setup
- **User permission**: Prompt users before downloading scripts to cache
- **Includes handling**: Symlink preferred, copy fallback for includes directory setup
- **Cache validation**: Check freshness, verify checksums, handle remote includes updates

16) Repository backend architecture
- **Bash backend**: `includes/repository.sh` with functions like `ensure_remote_includes()`, `download_script()`
- **Python backend**: `lib/repository.py` with equivalent functionality for GUI
- **Configuration**: `~/.lv_linux_learn/config.json` shared between CLI and GUI
- **Feature parity**: Identical capabilities in both bash and Python implementations
- **Error handling**: Graceful fallbacks from remote to local to cached includes

17) Bash compatibility notes
- Use `set -euo pipefail` in all new bash scripts
- Avoid bash array slicing syntax `${array[@]:start:length}` - build new arrays instead
- Arithmetic: use `count=$((count + 1))` instead of `((count++))` with strict mode
- No `local` keyword outside functions (main script body uses regular variables)
- Path handling: check if path starts with `/` for absolute paths before adding prefixes
- Repository context: Handle both local repository execution and cached execution contexts

18) AI agent development guidance
- **System understanding**: This is a multi-repository script management system with caching
- **Feature development**: Maintain feature parity between CLI (bash) and GUI (Python)
- **Repository compatibility**: New scripts should work in both local and cached contexts
- **Documentation updates**: Always update relevant docs/ files when adding features
- **Security focus**: Multi-repository support requires careful security considerations
- **Testing approach**: Test both local development and repository distribution scenarios
- **Configuration management**: Respect existing configuration patterns and file locations

If any section needs clarification or you want specific examples for modifying components (adding repository features, creating custom scripts, updating interfaces), specify the component and I'll provide concrete implementation patterns.
