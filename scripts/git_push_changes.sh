#!/bin/bash
# Script to commit changes to GitHub
set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Change to repo root
cd "$repo_root"

# Check if git user.name and user.email are configured
if ! git config --get user.name >/dev/null || ! git config --get user.email >/dev/null; then
  green_echo "[!] Git is not configured. Running git_setup.sh..."
  "$repo_root/scripts/git_setup.sh"
fi

# Check if there are changes to commit
if git diff-index --quiet HEAD -- 2>/dev/null; then
  green_echo "[!] No changes to commit"
  exit 0
fi

green_echo "[*] Current changes:"
git status --short

green_echo "[*] Staging changes..."
git add .

green_echo "[*] Committing changes..."
git commit

green_echo "[!] About to push changes to $(git remote get-url origin 2>/dev/null || echo 'origin')..."
read -rp "Press Enter to continue or Ctrl+C to cancel..."

green_echo "[*] Pushing changes..."
git push

green_echo "[+] Changes pushed successfully"
exit 0
