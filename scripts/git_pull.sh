#!/bin/bash
# Pull latest changes from git remote
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

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
