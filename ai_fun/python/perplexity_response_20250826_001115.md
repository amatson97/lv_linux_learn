# Perplexity API Response

## Prompt
Can you write me a docker compose for a plex server.
- nvidia gpu pass throug
- directory /oldhome/plex for config mounts.
- directories for media.
	- /raid10/movies
	-/raid10/music
	- /raid10/tvshows
	- /raid10/anime
## Response
Here is a Docker Compose file for running a **Plex Media Server** with **NVIDIA GPU passthrough** (hardware transcoding), mounting your specified config and media directories.

```yaml
version: "3.8"

services:
  plex:
    image: plexinc/pms-docker:latest
    container_name: plex
    restart: unless-stopped
    network_mode: host
    environment:
      - TZ=Europe/London           # Set your timezone
      - PLEX_CLAIM=               # Optional: Add your Plex claim token
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
      - PLEX_UID=1000             # Replace with your user ID if needed
      - PLEX_GID=1000             # Replace with your group ID if needed
    volumes:
      - /oldhome/plex:/config
      - /raid10/movies:/data/movies
      - /raid10/music:/data/music
      - /raid10/tvshows:/data/tvshows
      - /raid10/anime:/data/anime
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    runtime: nvidia
```

**Key details:**
- **NVIDIA GPU passthrough** is enabled via `runtime: nvidia` and the `NVIDIA_VISIBLE_DEVICES`/`NVIDIA_DRIVER_CAPABILITIES` environment variables. This requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed on your host[4][5].
- **Config directory** is mounted at `/oldhome/plex:/config` as required[2][3].
- **Media directories** are mounted at `/raid10/movies`, `/raid10/music`, `/raid10/tvshows`, and `/raid10/anime` to `/data/movies`, `/data/music`, `/data/tvshows`, and `/data/anime` inside the container[2][3].
- **network_mode: host** is recommended for Plex to allow best client discovery and direct play[5].
- **restart: unless-stopped** ensures Plex restarts unless manually stopped[2].
- Set your **timezone** and optionally your **PLEX_CLAIM** token for initial server claim[3][5].

**Additional notes:**
- Replace `PLEX_UID` and `PLEX_GID` with your actual user and group IDs for correct file permissions[3].
- If you want to use different container paths for your media, adjust the right-hand side of the volume mappings accordingly.
- Ensure your host has the NVIDIA drivers and container toolkit installed for GPU passthrough to work[4].

This configuration is based on current best practices for Plex with Docker and NVIDIA GPU support[3][4][5].
## Citations
- https://www.youtube.com/watch?v=xZrdkBJgDp4
- https://www.youtube.com/watch?v=Nnvp9YrTbXs
- https://pimylifeup.com/plex-docker/
- https://www.youtube.com/watch?v=rAqusFcc-38
- https://github.com/plexinc/pms-docker

