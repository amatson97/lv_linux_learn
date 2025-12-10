#!/bin/bash
# Script to set up Ubuntu 22.04+ with git and gh (GitHub CLI)
# Installs required packages, guides through authentication (HTTPS recommended for Ubuntu Desktop)
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

green_echo "[*] Checking for Git..."
if ! command -v git &> /dev/null; then
  green_echo "[*] Installing Git..."
  sudo apt update -y
  sudo apt install -y git
else
  green_echo "[+] Git is already installed ($(git --version | tr -d '\n'))"
fi

green_echo "[*] Checking for GitHub CLI (gh)..."
if ! command -v gh &> /dev/null; then
  green_echo "[*] Installing GitHub CLI..."
  sudo apt update -y
  sudo apt install -y gh
else
  green_echo "[+] GitHub CLI is already installed ($(gh --version | head -n1 | tr -d '\n'))"
fi

# Optional: configure global git identity if not set
if ! git config --global user.name &> /dev/null; then
  echo
  read -rp "Git user.name not set. Enter your name (or press Enter to skip): " git_name
  if [ -n "$git_name" ]; then
    git config --global user.name "$git_name"
    green_echo "[+] Set git user.name to '$git_name'"
  fi
fi

if ! git config --global user.email &> /dev/null; then
  read -rp "Git user.email not set. Enter your email (or press Enter to skip): " git_email
  if [ -n "$git_email" ]; then
    git config --global user.email "$git_email"
    green_echo "[+] Set git user.email to '$git_email'"
  fi
fi

# Guide through gh authentication if not already authenticated
green_echo "[*] Checking GitHub CLI authentication..."
if gh auth status &> /dev/null; then
  green_echo "[+] You are already authenticated with GitHub CLI."
else
  echo
  green_echo "[*] You need to authenticate GitHub CLI."
  echo "    Recommended: use HTTPS for Ubuntu Desktop (easier for GUI prompts)."
  echo "    Run: gh auth login"
  echo
  read -rp "Run 'gh auth login' now? (Y/n): " yn
  case "${yn:-y}" in
    [Yy]*)
      gh auth login
      if gh auth status &> /dev/null; then
        green_echo "[+] Successfully authenticated with GitHub CLI."
      else
        echo "[!] Authentication may have failed. Run 'gh auth login' manually if needed."
      fi
      ;;
    *)
      echo "[!] Skipped. Run 'gh auth login' manually when ready."
      ;;
  esac
fi

green_echo "[+] Setup complete! You can now use Git commands and GitHub CLI with HTTPS authentication."