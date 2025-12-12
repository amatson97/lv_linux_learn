# Advanced Topics

Advanced server configurations and enterprise tools.

## Table of Contents
1. [Nextcloud Server](#nextcloud-server)
2. [Traefik Reverse Proxy](#traefik-reverse-proxy)
3. [GitHub Workflows](#github-workflows)

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
