# References & Guides

Complete reference guides for tools, utilities, networking, Docker, AI tools, and advanced topics.

## Table of Contents
1. [Tools & Utilities](#tools--utilities)
2. [Bash Learning Exercises](#bash-learning-exercises)
3. [Docker & Containerization](#docker--containerization)
4. [Networking & VPN](#networking--vpn)
5. [AI Integration Tools](#ai-integration-tools)
6. [Advanced Topics](#advanced-topics)

---

## Tools & Utilities

The `tools/` directory contains utility scripts for file management and system optimization.

**Common features:**
- Extract 7z and zip files automatically
- Remove source archives after extraction
- Utilize RAM disk for increased performance during operations
- Batch processing capabilities

### Usage

```bash
# Navigate to tools directory
cd tools/

# Make scripts executable
chmod +x *.sh

# Run specific utility (check script comments for usage)
./script_name.sh
```

**Available tools:**
- `7z_extractor*.sh` — Archive extraction with RAM disk support
- `flac_to_mp3.sh` — Audio format conversion
- `convert_*.sh` — Various file format converters
- `check_power_on*.sh` — Check power-on hours of disks
- `extract-xiso/` — Xbox ISO extraction tool
- `git_pull.sh` — Batch Git repository updates
- `plex-batch-remux.sh` — Plex media file batch processing

### Linux Drive Management

Essential resources for disk and storage management:

- [Formatting Disks](https://phoenixnap.com/kb/linux-format-disk)
- [Mounting Disks](https://www.wikihow.com/Linux-How-to-Mount-Drive)
- [Linux Software RAID (mdadm)](https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm)
- [Disable USB Storage Quirk](https://forums.unraid.net/topic/170412-unraid-61210-how-to-permanently-add-a-usb-storage-quirk-to-disable-uas/)

---

## Bash Learning Exercises

The `bash_exercises/` directory contains 8 interactive scripts designed for learning bash fundamentals.

**Features:**
- Professional formatting with decorative headers and structured output
- Educational explanations describing concepts being demonstrated
- Error handling and validation for robust execution
- Interactive pauses so you can read output before returning to menu
- Multiple examples showing different ways to accomplish tasks
- Real-world usage tips and command variations

### Available Exercises

1. **hello_world.sh** - Classic first program with script structure explanation
2. **show_date.sh** - Date command with 5+ format examples (ISO 8601, Unix timestamp, 12-hour, etc.)
3. **list_files.sh** - Demonstrates `ls`, `ls -lh`, and `ls -lha` with permission display
4. **make_directory.sh** - Directory creation with input validation and existence checking
5. **print_numbers.sh** - For loops printing 1-10, shows brace expansion, seq, and C-style syntax
6. **simple_calculator.sh** - All 4 basic operations (+, -, ×, ÷) with regex input validation
7. **find_word.sh** - grep searching with file listing, match counting, and line numbers
8. **count_lines.sh** - wc command showing lines, words, characters, and bytes

**Run from the menu or directly:**
```bash
cd bash_exercises/
./hello_world.sh
./show_date.sh
# ... etc
```

---

## Docker & Containerization

Complete guide for Docker, containerization, and related services.

### Docker Installation

Docker enables containerized application deployment. The repository includes installation scripts and docker-compose examples.

⚠️ **Security Best Practices:**
- Never run containers as root unless absolutely necessary
- Always review Docker images from trusted sources
- Keep your Docker installation updated
- Use specific version tags instead of `latest` in production

#### Installation

```bash
# Run from the interactive menu, or directly:
./scripts/docker_install.sh
```

**What the script installs:**
- Docker Engine (CE)
- Docker CLI
- containerd
- Docker Buildx plugin
- Docker Compose plugin

**Post-installation:**
- Adds your user to the `docker` group (log out/in required)
- Enables Docker service at boot
- Runs `hello-world` container to verify installation

### Docker Commands

#### Container Commands

```bash
docker container [command]
```

Common commands include:
- `attach` – Connect to a running container
- `exec` – Execute a command in a container (e.g., `docker exec -it container_name bash`)
- `logs` – View container logs
- `ls` – List running containers (`docker ps` also works)
- `restart` – Restart containers
- `run` – Create & run a new container
- `stop` – Stop containers
- `rm` – Remove containers

#### Volume Commands

```bash
docker volume [command]
```

- `create` – Create a volume
- `inspect` – Show details
- `ls` – List volumes
- `prune` – Remove unused volumes
- `rm` – Delete volumes

#### Network Commands

```bash
docker network [command]
```

- `create` – Create a network
- `connect` – Attach a container to a network
- `disconnect` – Remove a container from a network
- `inspect` – View details
- `ls` – List networks
- `prune` – Remove unused networks
- `rm` – Delete networks

### Docker Compose

#### Commands

```bash
# Navigate to directory with docker-compose.yml first
cd docker-compose/

# Start containers in detached mode
docker compose up -d

# Stop and remove containers
docker compose down

# View running services
docker compose ps

# View logs
docker compose logs -f
```

#### Example Configuration

Example files can be found in:
```
docker-compose/docker-compose.yml
docker-compose/.env
```

### Portainer

Web-based Docker management interface.

- [Portainer Website](https://www.portainer.io/)
- [Install Guide (Docker/Linux)](https://docs.portainer.io/start/install/server/docker/linux)

⚠️ **Prerequisites**: Docker must be installed and running before installing Portainer.

### Plex Media Server

Run Plex Media Server inside Docker. Adjust the provided `docker-compose/docker-compose.yml` to fit your setup.

- [Plex Docker Hub (LinuxServer.io)](https://hub.docker.com/r/linuxserver/plex)

**Configuration Notes:**
- Ensure proper volume mappings for your media directories
- Set appropriate `PUID` and `PGID` for file permissions
- Consider using hardware transcoding if your system supports it

---

## Networking & VPN

Complete guide for ZeroTier VPN, network tools, and remote access.

### ZeroTier Network Tools

The `zerotier_tools/` directory contains utilities for managing and monitoring ZeroTier VPN networks.

#### Available Scripts

```bash
# Get IP addresses of network members
./zerotier_tools/get_ip.sh <API_TOKEN> <NETWORK_ID>

# Generate HTML report of network status
./zerotier_tools/html_ip.sh <API_TOKEN> <NETWORK_ID>

# Desktop notifications for network changes
./zerotier_tools/zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

### Automated Monitoring Setup

Configure desktop notifications for network member status changes:

```bash
# Edit crontab
crontab -e

# Add this line (replace placeholders with actual values)
*/5 * * * * DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/<USER>/lv_linux_learn/zerotier_tools/zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

**What it does:**
- Checks every 5 minutes for network member status changes
- Issues desktop notifications when nodes come online/offline
- Shows member names and IP addresses

**Note:** Contact the repository administrator for `<API_TOKEN>` and `<NETWORK_ID>` values.

### VPN Management

#### Uninstall All VPNs

Remove all VPN technologies from your machine:

```bash
./uninstallers/uninstall_all_vpn.sh
```

This removes:
- ZeroTier One
- NordVPN
- LogMeIn Hamachi (deprecated, but cleanup included for legacy systems)

You can then disable remote desktop features in system settings.

---

## AI Integration Tools

Complete guide for Perplexity AI CLI and desktop applications.

### Enhanced Perplexity CLI (v1.1)

**Status:** BETA

#### Features

- Multi-turn conversations with persistent context
- Streaming responses for faster feedback
- Multiple output formats (Plain, Markdown, JSON, Shell, Auto)
- Automatic Mermaid diagram support for workflows/architecture
- Client-side syntax highlighting (bat/pygmentize)
- Save responses to Markdown files

#### Installation

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Make script executable
chmod +x perplex_cli_v1.1.sh

# Run with API key (or set PERPLEXITY_API_KEY env var)
./perplex_cli_v1.1.sh <Your_API_Key>

# API key will be encrypted and saved to ~/.perplexity_api_key on first run
```

#### Requirements

- Perplexity API key (get from https://www.perplexity.ai/)
- **Security:** API keys are encrypted before storage using Fernet (AES 128) encryption
- **Recommended:** `jq`, `bat`, `fzf` for enhanced functionality
  ```bash
  sudo apt install -y jq bat fzf
  ```

#### Usage

```bash
# Interactive mode (default)
./perplex_cli_v1.1.sh

# Pipe mode for automation
echo "Explain Docker networking" | ./perplex_cli_v1.1.sh --cli
```

#### Interactive Commands

```
:help                 Show all commands
:exit                 Quit
:format <type>        Set format (Plain|Markdown|JSON|Shell|Auto)
:render <on|off>      Toggle client-side rendering
:stream <on|off>      Toggle streaming mode
:context <on|off>     Enable/disable conversation history
:history              View saved conversation context
:save <file>          Save last response to Markdown file
:clear                Clear the terminal
```

#### Example Session

```
perplexity> :format Markdown
Format set: Markdown

perplexity> :context on
Context ON

perplexity> Explain the OSI model with a diagram
Enter multi-line input; end with a line containing only EOF
EOF

[Response with Mermaid diagram will be displayed]

perplexity> :save osi_model.md
Saved to osi_model.md
```

### Legacy Perplexity Script

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Run with API key
./perplex.sh <Perplexity_API_Key>
```

**How it works:**
1. Enter your query when prompted
2. Type `EOF` on a new line to submit
3. Response rendered in markdown format
4. Option to export to `.md` file

### Python Desktop Applications

Desktop GUI versions are available in `ai_fun/python/` (v1.0-v1.4).

**Features:**
- GTK-based graphical interface
- Desktop integration with `.desktop` files
- Asset management for icons and resources
- Generated markdown file storage

**Location:**
```
ai_fun/python/
├── perplexity_desktop_v1.0.py
├── perplexity_desktop_v1.2.py
├── perplexity_desktop_v1.3.py
├── perplexity_desktop_v1.4.py
├── assets/
│   └── perplexity.desktop
└── generated_md_files/
```

---

## Advanced Topics

Advanced server configurations, enterprise development, and multi-repository deployment.

### Multi-Repository Development

Advanced usage of the multi-repository system for creating and managing custom script libraries.

#### Repository Structure Best Practices

```
your-script-library/
├── manifest.json                    # Repository manifest
├── includes/                        # Shared functions and utilities
│   ├── main.sh                     # Core functions (required)
│   ├── logging.sh                  # Logging utilities
│   └── validation.sh               # Input validation functions
├── scripts/                         # Installation scripts
│   ├── install-server.sh
│   └── install-client.sh
├── tools/                          # Utility tools
│   ├── backup-tool.sh
│   └── monitoring.sh
├── exercises/                      # Learning scripts
│   └── advanced-bash.sh
├── uninstallers/                   # Removal scripts
│   └── remove-server.sh
└── README.md                       # Repository documentation
```

#### Advanced Manifest Configuration

```json
{
  "version": "1.2.0",
  "repository_url": "https://raw.githubusercontent.com/yourorg/yourrepo/main",
  "min_app_version": "2.1.0",
  "description": "Enterprise script library for server management",
  "author": "Your Organization",
  "license": "MIT",
  "last_updated": "2025-12-13T12:00:00Z",
  "scripts": [
    {
      "id": "enterprise-server-install",
      "name": "Enterprise Server Setup",
      "category": "install",
      "version": "2.0.0",
      "file_name": "install-server.sh",
      "relative_path": "scripts/install-server.sh",
      "download_url": "https://raw.githubusercontent.com/yourorg/yourrepo/main/scripts/install-server.sh",
      "checksum": "sha256:abc123...",
      "description": "Complete enterprise server installation and configuration",
      "requires_sudo": true,
      "dependencies": ["docker", "nginx"],
      "tags": ["enterprise", "server", "production"]
    }
  ]
}
```

#### Development Workflow

**Local Development Setup:**

```bash
# Clone your repository
git clone https://github.com/yourorg/yourrepo.git
cd yourrepo

# Test scripts locally first
chmod +x scripts/*.sh tools/*.sh
./scripts/install-server.sh

# Test includes functionality
source includes/main.sh
green_echo "Testing shared functions"
```

**Manifest Generation:**

```bash
# Create a manifest generation script
#!/bin/bash
# generate_manifest.sh

REPO_URL="https://raw.githubusercontent.com/yourorg/yourrepo/main"

generate_checksum() {
    local file="$1"
    sha256sum "$file" | cut -d' ' -f1
}

# Generate manifest.json with current checksums
# (Customize based on your repository structure)
```

**Testing with lv_linux_learn:**

```bash
# Configure lv_linux_learn to use your repository
./menu.sh
# Select: 6) Script Repository
# Select: 6) Repository Settings  
# Select: m) Set Custom Manifest URL
# Enter: https://raw.githubusercontent.com/yourorg/yourrepo/main/manifest.json

# Test script downloads and execution
# Verify includes directory is downloaded correctly
# Check cache-first execution behavior
```

#### Enterprise Deployment

**Multi-Environment Setup:**

```bash
# Development repository
DEV_MANIFEST="https://raw.githubusercontent.com/yourorg/scripts-dev/main/manifest.json"

# Staging repository  
STAGING_MANIFEST="https://raw.githubusercontent.com/yourorg/scripts-staging/main/manifest.json"

# Production repository
PROD_MANIFEST="https://raw.githubusercontent.com/yourorg/scripts-prod/main/manifest.json"

# Configure per environment
export CUSTOM_MANIFEST_URL="$PROD_MANIFEST"
```

**CI/CD Integration:**

```yaml
# .github/workflows/validate-scripts.yml
name: Validate Script Repository

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Validate Script Syntax
      run: |
        find . -name "*.sh" -type f | while read script; do
          bash -n "$script"
        done
    
    - name: Generate and Validate Manifest
      run: |
        ./generate_manifest.sh
        jq empty manifest.json  # Validate JSON syntax
        
    - name: Test with lv_linux_learn
      run: |
        git clone https://github.com/amatson97/lv_linux_learn.git
        cd lv_linux_learn
        export CUSTOM_MANIFEST_URL="file://$PWD/../manifest.json"
        ./menu.sh << 'EOF'
        6
        5
        0
        EOF
```

#### Security Considerations

**Repository Security:**
1. **Code Signing**: Implement GPG signing for commits and releases
2. **Access Control**: Use private repositories for sensitive scripts
3. **Audit Logging**: Track who uses which scripts when
4. **Checksum Validation**: Always generate accurate SHA256 checksums

**Network Security:**
```bash
# Use HTTPS only for repository URLs
# Validate SSL certificates
# Consider VPN requirements for private repositories
```

### Nextcloud Server

Configure Nextcloud for cloud storage and file synchronization. See the installation scripts for automated setup.

### Traefik Reverse Proxy

Use Traefik for intelligent routing and SSL termination with Docker containers. Recommended for advanced deployments.

### GitHub Workflows

Implement CI/CD pipelines for:
- Automated script validation
- Manifest generation
- Test execution
- Release publishing
