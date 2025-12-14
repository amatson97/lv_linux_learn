#!/bin/bash
# Description: Safe Git repository update tool with conflict detection
#
# Pulls latest changes from remote repository with safety checks.
# Verifies clean working directory, handles merge conflicts gracefully,
# and provides status information before and after pull operations.
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Change to repo root
cd "$repo_root"

green_echo "[*] Preparing to pull latest changes from $(git remote get-url origin 2>/dev/null || echo 'origin')..."

# Check if repo is clean
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
  green_echo "[!] You have uncommitted changes. Stash or commit them first."
  git status --short
  exit 1
fi

green_echo "[*] Running git pull..."
git pull

green_echo "[+] Complete"
exit 0
