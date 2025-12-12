# Copilot / AI Agent Instructions — lv_linux_learn

Purpose: Help an AI coding agent be productive in this repo by summarizing architecture, conventions, workflows, and safe constraints discovered in the codebase.

1) Big picture
- This repository is a curated collection of Ubuntu-focused setup and utility scripts (mostly Bash) and small helper apps. Primary user flows are interactive installers and desktop helpers invoked from `./menu.sh` or `./menu.py`.
- Key responsibilities: install packages (`apt`), configure VPN/networking tools (ZeroTier, NordVPN, Hamachi), create desktop launchers, and provide utility tools under `tools/` and `scripts/`.

2) Entry points & important paths
- Run interactive menu: `./launcher.sh` (auto-detects GUI vs CLI), `./menu.sh` (bash CLI), or `./menu.py` (Python GUI). These are the most common developer/test entry points.
- Shared shell functions: `includes/main.sh` — prefer adding global helpers here and `source` it from scripts.
- Main script directories: `scripts/`, `tools/`, `zerotier_tools/`, `docker-compose/`, `ai_fun/`, `bash_exercises/`, `uninstallers/`, `examples/`.
- Documentation: `docs/` contains topic-specific guides (INSTALLATION.md, DOCKER.md, TROUBLESHOOTING.md, etc.). Main README.md is streamlined to <250 lines.
- Custom scripts: `~/.lv_linux_learn/custom_scripts.json` stores user-added scripts (shared between menu.py and menu.sh).

3) Coding & style conventions (project-specific)
- Shell flavor: scripts use `#!/bin/bash`. Use bash-compatible constructs (arrays, `[[ ... ]]`) rather than strict POSIX `sh` unless you intentionally change a script.
- Logging: use the existing `green_echo` helper for status messages. Follow its pattern for consistent output.
- Shared helpers: put reusable functions in `includes/main.sh`. New scripts should `source includes/main.sh` where they rely on shared helpers.
- Execution assumptions: many scripts assume they're run from the repo root and sometimes reference `$HOME/lv_linux_learn`. Prefer absolute `$HOME` expansions and note where code uses repo-root-relative paths.
- Desktop integration: desktop launchers and small helper scripts are created under `$HOME/.lv_connect` and `$HOME/Desktop`. Use `gio set <file> metadata::trusted true` when creating `.desktop` files.

4) Safety, secrets & sensitive state
- There are hard-coded tokens/IDs in scripts (example: `NORDVPN_TOKEN` in `includes/main.sh`). Do NOT expose, modify, or commit secrets. If a change requires a token, prompt the repo owner or add configuration to read it from environment variables instead.
- Network identifiers (ZeroTier network IDs, Hamachi networks) appear in scripts. Confirm with the owner before changing those values.

5) Developer workflows & testing
- Quick local test: make scripts executable then run the menu and the target script:

  chmod +x scripts/*.sh includes/*.sh *.sh
  ./menu.sh

- For individual scripts: run `./scripts/foo.sh` or `bash scripts/foo.sh` and observe `green_echo` output and created artifacts in `$HOME`.
- There are no automated tests — validate manually on an Ubuntu Desktop VM (the README recommends Ubuntu 24.04.3 LTS).
- **Testing menu.sh with heredoc** (automated input):
  ```bash
  ./menu.sh << 'EOF'
  5
  d
  2
  y
  0
  EOF
  ```

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
- `docs/` — detailed topic-specific guides (INSTALLATION.md, DOCKER.md, TROUBLESHOOTING.md, NETWORKING.md, TOOLS.md, AI_TOOLS.md, ADVANCED.md).
- `includes/main.sh` — shared helpers and conventions.
- `menu.sh`, `menu.py` — entry points and menu system architecture.
- `scripts/`, `tools/`, `ai_fun/`, `uninstallers/` — examples of patterns and how installers/uninstallers are implemented.

11) Menu system architecture (menu.sh)
- **Hierarchical navigation**: 5 main categories (Install, Tools, Exercises, Uninstall, Custom Scripts) with drill-down functionality.
- **SCRIPTS array index ranges** (critical when adding new scripts):
  - Install: 0-8 (9 scripts)
  - Tools: 10-20 (11 scripts)
  - Exercises: 22-29 (8 scripts)
  - Uninstall: 31-41 (11 scripts)
  - Custom: 43+ (dynamic, loaded from JSON)
- **Important**: When adding scripts to SCRIPTS/DESCRIPTIONS arrays, update the index ranges in `show_menu()` function's case statement.
- **Display-to-index mapping**: `DISPLAY_TO_INDEX` array maps displayed numbers (1,2,3...) to actual array indices in category views.

12) Custom script system
- **Storage**: `~/.lv_linux_learn/custom_scripts.json` (shared between GUI and CLI)
- **Key functions** in menu.sh:
  - `load_custom_scripts()` - Appends custom scripts from JSON to SCRIPTS/DESCRIPTIONS arrays
  - `reload_custom_scripts()` - Truncates arrays at index 42, then reloads (for instant updates)
  - `add_custom_script()` - Interactive CLI for adding scripts (supports cancel at any prompt)
  - `edit_custom_script()` - Edit existing custom scripts (GUI has right-click, CLI has 'e' command)
  - `delete_custom_script()` - Delete custom scripts with confirmation (GUI has right-click, CLI has 'd' command)
- **Pattern**: Always call `reload_custom_scripts()` after add/edit/delete operations for instant menu updates (no restart needed).
- Custom scripts display with 📝 emoji prefix in both interfaces.

13) Documentation strategy
- **Main README.md**: Keep under 250 lines, focus on quick start, link to detailed docs
- **Topic guides in docs/**: Comprehensive coverage of specific areas
- **When adding features**: Update both README.md (brief mention) and relevant docs/ file (detailed guide)
- **New topics**: Create new file in docs/ rather than bloating README.md

14) Bash compatibility notes
- Use `set -euo pipefail` in all new bash scripts
- Avoid bash array slicing syntax `${array[@]:start:length}` - build new arrays instead
- Arithmetic: use `count=$((count + 1))` instead of `((count++))` with strict mode
- No `local` keyword outside functions (main script body uses regular variables)
- Path handling: check if path starts with `/` for absolute paths before adding prefixes

If any section is unclear or you want me to expand examples for modifying a particular script (for example, adding a new installer to `scripts/` or a new category to menu.sh), tell me which file to update and I'll propose a concrete patch.
