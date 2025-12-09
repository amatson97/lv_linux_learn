# Perplexity API Response

## Prompt
```
Write me a docker compose for a plex media server with nvidia gpu passthrough for hardware transcoding.
```

## Response
Here is a minimal `docker-compose.yml` that runs **Plex with NVIDIA GPU passthrough** for hardware transcoding, using the official Plex image and the NVIDIA container runtime:

```yaml
version: "3.8"

services:
  plex:
    image: plexinc/pms-docker:plexpass   # or :latest if you don't have Plex Pass
    container_name: plex
    restart: unless-stopped

    # Use the NVIDIA container runtime
    runtime: nvidia

    environment:
      - TZ=America/New_York              # set your timezone
      - PLEX_CLAIM=claim-xxxxxxxx       # optional, from plex.tv/claim
      - ADVERTISE_IP=http://your.ip.or.hostname:32400/
      - NVIDIA_VISIBLE_DEVICES=all      # or a specific GPU UUID
      - NVIDIA_DRIVER_CAPABILITIES=video,compute,utility

      # Optional user mapping (change to match your UID/GID)
      - PLEX_UID=1000
      - PLEX_GID=1000

    ports:
      - "32400:32400/tcp"
      - "3005:3005/tcp"
      - "8324:8324/tcp"
      - "32469:32469/tcp"
      - "1900:1900/udp"
      - "32410:32410/udp"
      - "32412:32412/udp"
      - "32413:32413/udp"
      - "32414:32414/udp"

    volumes:
      # Plex config & database
      - /path/to/plex/config:/config
      # Transcode temp dir (RAM or fast SSD recommended)
      - /dev/shm:/transcode
      # Your media libraries
      - /path/to/movies:/data/movies
      - /path/to/tv:/data/tv
      - /path/to/music:/data/music
```

Key points to make this work:

- On the **host**, install the NVIDIA driver and **nvidia-container-toolkit** so Docker supports `--runtime=nvidia` / `runtime: nvidia`.[1][2]  
- After installing the toolkit, restart Docker and verify with:  
  `docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi`.[1]  
- In Plex’s web UI, enable **Settings → Transcoder → Use hardware-accelerated video encoding/decoding**.  
- If you want to restrict to one GPU, set `NVIDIA_VISIBLE_DEVICES` to that GPU’s UUID (from `nvidia-smi --query-gpu=gpu_name,gpu_uuid --format=csv`).[2]

## Citations
- https://www.raglits.co.uk/plex-docker-container-with-nvidia-transoding/
- https://github.com/linuxserver/docker-plex
- https://forums.truenas.com/t/can-the-official-plex-docker-use-nvidia-gpu-transcoding-through-compose/34329
- https://discourse.linuxserver.io/t/gpu-support-in-container/3139
- https://github.com/plexinc/pms-docker
- https://www.youtube.com/watch?v=VbNABbeZC-Y
- https://forums.plex.tv/t/pms-hardware-encoding-works-at-first-then-breaks-after-a-while/791678
