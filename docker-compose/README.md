# Docker Compose Configurations

This directory contains Docker Compose configurations for containerized services and applications.

## Contents

### Docker Compose Files
- **docker-compose.yml** - Main Docker Compose configuration for multi-container setup

### Installation Scripts
- **wordpress_install.sh** - WordPress installation and setup script

## Purpose

This directory provides:
- **Container orchestration** - Multi-container environment definitions
- **Service integration** - Pre-configured services (WordPress, databases, etc.)
- **Development environments** - Quick setup for testing and development
- **Deployment configuration** - Production-ready compose files

## Usage

### Basic Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up -d --build
```

### WordPress Setup

Use the included script to install and configure WordPress:

```bash
bash wordpress_install.sh
```

## Requirements

- Docker Engine
- Docker Compose
- Sufficient disk space
- Required ports available (80, 443, 3306, etc.)

## Configuration

Edit `docker-compose.yml` to customize:
- Port mappings
- Environment variables
- Volume mounts
- Service dependencies
- Resource limits

## Related Directories

- **../scripts/** - Shell installation scripts
- **../tools/** - Utility tools
- **../docs/guides/** - Usage guides

## Status

✅ Production Ready - All configurations tested and documented
