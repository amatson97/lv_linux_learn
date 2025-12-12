# Docker Guide

Complete guide for Docker, containerization, and related services.

## Table of Contents
1. [Docker Installation](#docker-installation)
2. [Docker Commands](#docker-commands)
3. [Docker Compose](#docker-compose)
4. [Portainer](#portainer)
5. [Plex Media Server](#plex-media-server)

---

## Docker Installation

Docker enables containerized application deployment. The repository includes installation scripts and docker-compose examples.

⚠️ **Security Best Practices:**
- Never run containers as root unless absolutely necessary
- Always review Docker images from trusted sources
- Keep your Docker installation updated
- Use specific version tags instead of `latest` in production

### Installation

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

### Official Documentation
- [Docker Docs](https://docs.docker.com)

---

## Docker Commands

### Container Commands

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

### Volume Commands

```bash
docker volume [command]
```

- `create` – Create a volume
- `inspect` – Show details
- `ls` – List volumes
- `prune` – Remove unused volumes
- `rm` – Delete volumes

### Network Commands

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

---

## Docker Compose

### Commands

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

### Example Configuration

Example files can be found in:
```
docker-compose/docker-compose.yml
docker-compose/.env
```

---

## Portainer

Web-based Docker management interface.

- [Portainer Website](https://www.portainer.io/)
- [Install Guide (Docker/Linux)](https://docs.portainer.io/start/install/server/docker/linux)

⚠️ **Prerequisites**: Docker must be installed and running before installing Portainer.

---

## Plex Media Server

You can run Plex Media Server inside Docker. Adjust the provided `docker-compose/docker-compose.yml` to fit your setup.

- [Plex Docker Hub (LinuxServer.io)](https://hub.docker.com/r/linuxserver/plex)

**Configuration Notes:**
- Ensure proper volume mappings for your media directories
- Set appropriate `PUID` and `PGID` for file permissions
- Consider using hardware transcoding if your system supports it
