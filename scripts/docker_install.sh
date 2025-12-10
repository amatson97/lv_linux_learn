#!/usr/bin/env bash
# Robust, idempotent Docker install for Ubuntu/Debian
set -euo pipefail

# repo-aware helpers
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

# Use sudo when not root
if [ "$(id -u)" -ne 0 ]; then
  SUDO=sudo
else
  SUDO=
fi

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Quick check: already installed?
if command_exists docker && docker --version >/dev/null 2>&1; then
  green_echo "[+] Docker already installed: $(docker --version | tr -d '\n')"
  exit 0
fi

green_echo "[*] Preparing to install Docker..."

# Install prerequisites
$SUDO apt-get update -y
$SUDO apt-get install -y --no-install-recommends ca-certificates curl gnupg lsb-release

# Create keyrings dir
KEYRING_DIR="/etc/apt/keyrings"
KEYRING_FILE="$KEYRING_DIR/docker.gpg"
$SUDO mkdir -p "$KEYRING_DIR"
$SUDO chmod 0755 "$KEYRING_DIR"

green_echo "[*] Fetching Docker official GPG key..."
# Download and dearmor into keyring (atomic)
if curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o "$KEYRING_FILE"; then
  $SUDO chmod 0644 "$KEYRING_FILE"
else
  log_err "Failed to fetch/dearmor Docker GPG key."
  exit 1
fi

# Determine codename (VERSION_CODENAME) with fallbacks
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  CODENAME="${VERSION_CODENAME:-}"
fi
if [ -z "${CODENAME:-}" ]; then
  if command_exists lsb_release; then
    CODENAME="$(lsb_release -cs)"
  fi
fi
if [ -z "${CODENAME:-}" ]; then
  log_err "Could not determine distribution codename (VERSION_CODENAME)."
  exit 1
fi

ARCH="$(dpkg --print-architecture 2>/dev/null || true)"
if [ -z "$ARCH" ]; then
  log_err "Unable to determine system architecture."
  exit 1
fi

LIST_FILE="/etc/apt/sources.list.d/docker.list"
green_echo "[*] Adding Docker apt repository (codename: ${CODENAME}, arch: ${ARCH})..."
$SUDO bash -c "cat > '$LIST_FILE' <<EOF
deb [arch=${ARCH} signed-by=${KEYRING_FILE}] https://download.docker.com/linux/ubuntu ${CODENAME} stable
EOF
"
$SUDO chmod 0644 "$LIST_FILE"

green_echo "[*] Updating apt and installing Docker packages..."
$SUDO apt-get update -y

# Install packages (use apt so dependencies resolved)
$SUDO apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin || {
  log_err "[!] apt install failed; attempting .deb fallback"
  TMPDIR="$(mktemp -d)"
  trap 'rm -rf \"$TMPDIR\"' EXIT
  DEB="$TMPDIR/docker.deb"
  curl -fsSL -o "$DEB" "https://download.docker.com/linux/static/stable/$(uname -m)/docker-20.10.24.tgz" 2>/dev/null || true
  # If apt failed and no static archive available, try installing google-chrome-style .deb fallback is not applicable here.
  log_err "Fallback did not install Docker. Please review output."
  exit 2
}

green_echo "[*] Enabling and starting Docker service..."
$SUDO systemctl enable --now docker.service || $SUDO systemctl start docker.service || true

# Add current user to docker group for convenience
if [ -n "${SUDO:-}" ]; then
  CURRENT_USER="${SUDO_USER:-${USER:-}}"
else
  CURRENT_USER="$(whoami)"
fi

if id -nG "$CURRENT_USER" | grep -qw docker; then
  green_echo "[*] User '$CURRENT_USER' is already in 'docker' group."
else
  green_echo "[*] Adding user '$CURRENT_USER' to 'docker' group (you may need to log out/in)..."
  $SUDO groupadd -f docker
  $SUDO usermod -aG docker "$CURRENT_USER" || log_err "Failed to add $CURRENT_USER to docker group; you may need to run manually."
fi

# Verify installation
if command_exists docker; then
  green_echo "[+] Docker installed: $(docker --version | tr -d '\n')"
  green_echo "[*] Testing 'docker run hello-world' (this may download an image)..."
  if docker run --rm hello-world >/dev/null 2>&1; then
    green_echo "[+] hello-world ran successfully."
  else
    green_echo "[!] 'docker run hello-world' failed (network or permission issue). Try: sudo docker run hello-world"
  fi
else
  log_err "Docker binary not found after installation."
  exit 3
fi

green_echo "[+] Installation complete."

exit 0