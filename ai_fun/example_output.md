Below is a sample `docker-compose.yml` and `.env` file that allow you to 
control the **exposed GPU**, **media shares**, **image version**, **network 
mode**, and **restart policy** for a Plex Media Server container. This setup 
uses the popular `linuxserver/plex` image, which supports NVIDIA GPU 
passthrough via Docker's `runtime: nvidia` option.

---

### `.env` file

```env
# Plex Docker Compose Environment

# GPU device to expose (e.g., all, 0, or leave empty for no GPU)
PLEX_GPU=all

# Media share paths (host paths)
MOVIES_PATH=/mnt/media/movies
TVSHOWS_PATH=/mnt/media/tvshows
MUSIC_PATH=/mnt/media/music
ANIME_PATH=/mnt/media/anime

# Plex image version (e.g., latest, 1.32.5, etc.)
PLEX_IMAGE_VERSION=latest

# Network mode (e.g., bridge, host)
PLEX_NETWORK_MODE=host

# Restart policy (e.g., unless-stopped, always, on-failure)
PLEX_RESTART_POLICY=unless-stopped
```

---

### `docker-compose.yml` file

```yaml
version: "3.8"

services:
  plex:
    image: linuxserver/plex:${PLEX_IMAGE_VERSION}
    container_name: plex
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
      # Uncomment and set your Plex claim token if needed
      # - PLEX_CLAIM=your_plex_claim_token
    volumes:
      - ./config:/config
      - ${MOVIES_PATH}:/data/movies
      - ${TVSHOWS_PATH}:/data/tvshows
      - ${MUSIC_PATH}:/data/music
      - ${ANIME_PATH}:/data/anime
    network_mode: ${PLEX_NETWORK_MODE}
    restart: ${PLEX_RESTART_POLICY}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: ${PLEX_GPU}
              capabilities: [gpu]
    # If you are not using Docker Swarm, use the following instead of 'deploy':
    # runtime: nvidia
    # devices:
    #   - /dev/nvidia0:/dev/nvidia0 # or /dev/nvidiactl, /dev/nvidia-uvm, etc.
    # Uncomment the lines above and adjust as needed for non-Swarm setups
```

---

**Notes and Usage:**

- **GPU Exposure:**  
  The `deploy.resources.reservations.devices` section is for Docker Swarm.  
  For standalone Docker Compose, use the commented `runtime: nvidia` and 
`devices:` lines instead.  
  You must have the [NVIDIA Container 
Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/insta
ll-guide.html) installed.

- **Media Shares:**  
  Set your actual host paths in the `.env` file. These will be mounted inside 
the container as `/data/movies`, `/data/tvshows`, etc.

- **Image Version:**  
  Change `PLEX_IMAGE_VERSION` in the `.env` file to use a specific version or 
`latest`.

- **Network Mode:**  
  `host` mode is recommended for Plex to allow proper DLNA and local discovery, 
but you can use `bridge` if you prefer.

- **Restart Policy:**  
  Set as needed in the `.env` file.

- **Plex Claim Token:**  
  For first-time setup, you may need to set `PLEX_CLAIM` (see [Plex docs][4]).

- **User/Group IDs:**  
  Adjust `PUID` and `PGID` as needed for your system permissions.

This configuration is based on best practices from community guides and the 
official documentation[1][2][4][5]. Adjust paths and settings to fit your 
environment.

Citations:
- https://www.rapidseedbox.com/blog/plex-on-docker
- https://pimylifeup.com/plex-docker/
- https://www.youtube.com/watch?v=xZrdkBJgDp4
- https://github.com/plexinc/pms-docker
- https://fullmetalbrackets.com/blog/setting-up-plex-in-docker/