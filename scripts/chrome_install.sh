#!/usr/bin/env bash
# Description: Install Google Chrome browser with automatic repository setup
#
# Installs the latest stable Google Chrome browser from official Google repository.
# Handles GPG key management, repository configuration, and package installation.
# Idempotent design - safe to run multiple times without issues.
# Change1
set -euo pipefail

# Source shared helpers (provides green_echo)
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Helpers
log_err() { printf '\033[1;31m%s\033[0m\n' "$*" >&2; }
cleanup() { [ -n "${TMPDIR:-}" ] && rm -rf "$TMPDIR" || true; }
trap cleanup EXIT

# Verify running on supported distro (Debian/Ubuntu family)
if [ -f /etc/os-release ]; then
  . /etc/os-release
  case "${ID:-}" in
    ubuntu|debian|linuxmint|pop) ;;
    *) green_echo "Warning: this script is tested on Debian/Ubuntu. Proceeding may fail."; ;;
  esac
fi

# Check architecture
ARCH="$(dpkg --print-architecture 2>/dev/null || echo unknown)"
if [ "$ARCH" != "amd64" ] && [ "$ARCH" != "x86_64" ]; then
  log_err "Unsupported architecture: $ARCH. Google Chrome .deb is only provided for amd64 on Debian/Ubuntu."
  exit 1
fi

# If Chrome already installed, show version and exit
if command -v google-chrome-stable >/dev/null 2>&1; then
  CURVER="$(google-chrome-stable --version 2>/dev/null || true)"
  green_echo "Google Chrome already installed: ${CURVER:-(unknown version)}"
  exit 0
fi

TMPDIR="$(mktemp -d)"
KEYRING_PATH="/usr/share/keyrings/google-linux-signing-keyring.gpg"
LIST_FILE="/etc/apt/sources.list.d/google-chrome.list"

green_echo "[*] Updating package lists and installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends wget ca-certificates gnupg curl apt-transport-https

green_echo "[*] Fetching Google's signing key and installing keyring..."
# Use gpg dearmor into keyring path
if command -v gpg >/dev/null 2>&1; then
  sudo mkdir -p "$(dirname "$KEYRING_PATH")"
  curl -fsSL "https://dl.google.com/linux/linux_signing_key.pub" | sudo gpg --dearmor -o "$KEYRING_PATH"
else
  # fallback: store raw pubkey (older apt-key style) but keep signed-by if possible
  curl -fsSL "https://dl.google.com/linux/linux_signing_key.pub" -o "$TMPDIR/google_signing_key.pub"
  sudo mkdir -p "$(dirname "$KEYRING_PATH")"
  sudo gpg --dearmor -o "$KEYRING_PATH" "$TMPDIR/google_signing_key.pub" 2>/dev/null || sudo cp "$TMPDIR/google_signing_key.pub" "${KEYRING_PATH}.pub"
fi

green_echo "[*] Adding Google's apt repository..."
# Write sources.list entry using signed-by if keyring exists
if [ -f "$KEYRING_PATH" ]; then
  echo "deb [arch=amd64 signed-by=$KEYRING_PATH] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee "$LIST_FILE" >/dev/null
else
  echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee "$LIST_FILE" >/dev/null
fi

green_echo "[*] Updating apt and installing Google Chrome..."
sudo apt-get update -y
# Install google-chrome-stable package (apt will resolve deps)
if sudo apt-get install -y google-chrome-stable; then
  green_echo "[+] Google Chrome installed successfully."
else
  log_err "apt install failed; attempting dpkg fallback."
  # Try direct download + dpkg install fallback
  DEB="$TMPDIR/google-chrome-stable_current_amd64.deb"
  wget -q -O "$DEB" "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
  sudo dpkg -i "$DEB" || sudo apt-get install -f -y
  if command -v google-chrome-stable >/dev/null 2>&1; then
    green_echo "[+] Google Chrome installed via .deb fallback."
  else
    log_err "Installation failed. See output above for details."
    exit 2
  fi
fi

green_echo "[*] Verifying installation..."
if command -v google-chrome-stable >/dev/null 2>&1; then
  google-chrome-stable --version || true
else
  log_err "google-chrome-stable command not found after install."
  exit 3
fi

# Avoid duplicate launcher icons: remove the legacy `com.google.Chrome.desktop`
# entry if the canonical `google-chrome.desktop` exists alongside it.
# This keeps the Ubuntu launcher from showing two Chrome icons and preserves
# the preferred `google-chrome.desktop` naming convention.
if [ -f /usr/share/applications/com.google.Chrome.desktop ] && [ -f /usr/share/applications/google-chrome.desktop ]; then
  green_echo "[*] Removing duplicate desktop entry /usr/share/applications/com.google.Chrome.desktop"
  sudo rm -f /usr/share/applications/com.google.Chrome.desktop || true
  sudo update-desktop-database >/dev/null 2>&1 || true
fi

green_echo "[*] Cleaning up..."
cleanup

green_echo "[+] Done."
exit 0