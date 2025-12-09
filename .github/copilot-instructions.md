# Copilot / AI Agent Instructions — lv_linux_learn

Purpose: Help an AI coding agent be productive in this repo by summarizing architecture, conventions, workflows, and safe constraints discovered in the codebase.

1) Big picture
- This repository is a curated collection of Ubuntu-focused setup and utility scripts (mostly Bash) and small helper apps. Primary user flows are interactive installers and desktop helpers invoked from `./menu.sh` or `./menu.py`.
- Key responsibilities: install packages (`apt`), configure VPN/networking tools (ZeroTier, NordVPN, Hamachi), create desktop launchers, and provide utility tools under `tools/` and `scripts/`.

2) Entry points & important paths
- Run interactive menu: `./menu.sh` (bash) or `./menu.py` (Python GUI). These are the most common developer/test entry points.
- Shared shell functions: `includes/main.sh` — prefer adding global helpers here and `source` it from scripts.
- Main script directories: `scripts/`, `tools/`, `zerotier_tools/`, `docker-compose/`, `ai_fun/`, `bash_exercises/`.

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
- `README.md` — project overview and workflows.
- `includes/main.sh` — shared helpers and conventions.
- `menu.sh`, `menu.py` — entry points.
- `scripts/`, `tools/`, `ai_fun/` — examples of patterns and how installers are implemented.

If any section is unclear or you want me to expand examples for modifying a particular script (for example, adding a new Docker installer under `scripts/`), tell me which file to update and I'll propose a concrete patch.
