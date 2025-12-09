# Perplexity API Response

## Prompt
```
Write me a bash script to install google chrome
```

## Response
Here is a simple Bash script that installs **Google Chrome Stable** on a Debian/Ubuntu-based system (64‑bit):

```bash
#!/usr/bin/env bash
set -e

# Must be run as root or with sudo
if [[ $EUID -ne 0 ]]; then
  echo "Please run as root, e.g.: sudo $0"
  exit 1
fi

# Detect architecture (only 64‑bit Chrome is officially provided)
ARCH=$(dpkg --print-architecture)
if [[ "$ARCH" != "amd64" ]]; then
  echo "Unsupported architecture: $ARCH"
  echo "Google Chrome for Linux is only provided for 64‑bit (amd64)."
  exit 1
fi

echo "Updating package index..."
apt update -y

echo "Installing prerequisites..."
apt install -y wget gnupg

echo "Adding Google Chrome repository key..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
  | gpg --dearmor \
  | tee /usr/share/keyrings/google-chrome.gpg >/dev/null

echo "Adding Google Chrome APT repository..."
cat >/etc/apt/sources.list.d/google-chrome.list <<EOF
deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main
EOF

echo "Updating package index with new repo..."
apt update -y

echo "Installing Google Chrome Stable..."
apt install -y google-chrome-stable

echo "Google Chrome installation complete."
echo "You can start it with: google-chrome"
```

Save this as e.g. `install_chrome.sh`, then run:

```bash
chmod +x install_chrome.sh
sudo ./install_chrome.sh
```

## Citations
- https://gist.github.com/diloabininyeri/637f0353394b95ade468d340f5079ad6
- https://www.geeksforgeeks.org/linux-unix/how-to-install-chrome-in-ubuntu/
- https://www.youtube.com/watch?v=Kd-c_CDEacQ
- https://www.petergirnus.com/blog/how-to-install-google-chrome-on-debian-linux
- https://support.google.com/chrome/a/answer/9025903?hl=en
