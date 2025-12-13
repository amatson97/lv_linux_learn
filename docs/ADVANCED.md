# Advanced Topics

Advanced server configurations, enterprise tools, and multi-repository development.

## Table of Contents
1. [Multi-Repository Development](#multi-repository-development)
2. [Nextcloud Server](#nextcloud-server)
3. [Traefik Reverse Proxy](#traefik-reverse-proxy)
4. [GitHub Workflows](#github-workflows)

---

## Multi-Repository Development

Advanced usage of the multi-repository system for creating and managing custom script libraries.

### Creating Production-Ready Custom Repositories

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

### Development Workflow

#### 1. Local Development Setup

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

#### 2. Manifest Generation

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

#### 3. Testing with lv_linux_learn

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

### Enterprise Deployment

#### Multi-Environment Setup

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

#### CI/CD Integration

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

### Security Considerations

#### Repository Security

1. **Code Signing**: Implement GPG signing for commits and releases
2. **Access Control**: Use private repositories for sensitive scripts
3. **Audit Logging**: Track who uses which scripts when
4. **Checksum Validation**: Always generate accurate SHA256 checksums

#### Network Security

```bash
# Use HTTPS only for repository URLs
# Validate SSL certificates
# Consider VPN requirements for private repositories
```

### Performance Optimization

#### Large Repository Handling

```bash
# For repositories with many scripts:
# 1. Implement lazy loading in manifest
# 2. Use script categories effectively
# 3. Consider repository splitting by function
# 4. Implement delta updates where possible
```

#### Bandwidth Optimization

```json
{
  "scripts": [
    {
      "id": "large-script",
      "compressed": true,
      "compression": "gzip",
      "compressed_checksum": "sha256:...",
      "uncompressed_checksum": "sha256:..."
    }
  ]
}
```

---

## Nextcloud Server

Install Nextcloud Desktop Client via Flatpak:

```bash
# Run from the interactive menu, or directly:
./scripts/nextcloud_client.sh
```

For server installation (without Traefik or Cloudflare configuration):
- [Nextcloud All-in-One Install Guide](https://nextcloud.com/blog/how-to-install-the-nextcloud-all-in-one-on-linux/)

**Security Considerations:**
- Change default passwords immediately
- Enable two-factor authentication
- Regular security updates are essential

---

## Traefik Reverse Proxy

Traefik is a modern reverse proxy and load balancer for microservices.

### Recommended Learning Order

1. [Introduction](https://doc.traefik.io/traefik/)
2. [Core Concepts](https://doc.traefik.io/traefik/getting-started/concepts/)
3. [FAQ](https://doc.traefik.io/traefik/getting-started/faq/)
4. [Configuration Overview](https://doc.traefik.io/traefik/getting-started/configuration-overview/)
5. [Providers Overview](https://doc.traefik.io/traefik/providers/overview/)
6. [Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
7. [Quick Start Guide](https://doc.traefik.io/traefik/getting-started/quick-start/)

---

## GitHub Workflows

### Recommended Learning Order

1. [About GitHub](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git)
2. [Start Your Journey](https://docs.github.com/en/get-started/start-your-journey)
3. [Setting up Git](https://docs.github.com/en/get-started/git-basics/set-up-git)
4. [Quick Start for Repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories)
5. [Managing Files](https://docs.github.com/en/repositories/working-with-files/managing-files)

### Repository Setup

```bash
# Install Git and GitHub CLI (automated)
./scripts/git_setup.sh

# This script will:
# 1. Install git and gh packages
# 2. Configure git user.name and user.email (if not set)
# 3. Guide you through 'gh auth login' for GitHub authentication
```
