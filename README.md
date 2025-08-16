# Linux Learning Guide
Support for Ubuntu Desktop 24.04.3 LTS
This guide is for the purposes of setting or a localhost enviroment. It will not cover installing and configuring public exopsed services.

## Useful command reference for beginners:

[https://www.hostinger.com/tutorials/linux-commands](https://www.hostinger.com/tutorials/linux-commands)

# Install scripts
I have included some usefual automated install scripts.

## list of bash install scripts
```bash
./install_remote_assist.sh
```

```bash
./uninstall_remote_assist.sh
```

```bash
./sublime_install.sh
```

```bash
./sublime.merge_install.sh
```

```bash
./chrome_install.sh
```

```bash
/docker_install.sh
```

## installation of remote assistance
```bash
sudo chmod +x install_remote_assist.sh
```
```bash
./install_remote_assist.sh
```
```bash
sudo reboot
```
```bash
./install_remote_assist.sh
```
Run Desktop Icon "Remote Desktop Info".

## Uninstall Remote assistance
```bash
sudo chmod +x uninstall_remote_assist.sh
```
```bash
./uninstall_remote_assist.sh
```

# Linux Drive Management

## Formatting Disks

[https://phoenixnap.com/kb/linux-format-disk](https://phoenixnap.com/kb/linux-format-disk)

## Mounting Disks

[https://www.wikihow.com/Linux-How-to-Mount-Drive](https://www.wikihow.com/Linux-How-to-Mount-Drive)

## Linux software raid

[https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm](https://www.ricmedia.com/tutorials/create-a-linux-raid-array-using-mdadm)

# Docker
Some basic docker commands for managing containers, volumes and networks. I will also look to putting in some docker-compose files for building services.

## Useful Links

[Official Docker documentation](https://docs.docker.com)

## Basic docker-compose commands
```bash
docker compose up -d
```

```bash
docker compose down
```

## Basic docker container commands
```bash
sudo docker container 

```

attach   (Attach local standard input, output, and error streams to a running container)

commit   (Create a new image from a container's changes)

cp       (Copy files/folders between a container and the local filesystem)

create   (Create a new container)

diff     (Inspect changes to files or directories on a container's filesystem)

exec     (Execute a command in a running container)

export   (Export a container's filesystem as a tar archive)

inspect  (Display detailed information on one or more containers)

kill     (Kill one or more running containers)

logs     (Fetch the logs of a container)

ls       (List containers)

pause    (Pause all processes within one or more containers)

port     (List port mappings or a specific mapping for the container)

prune    (Remove all stopped containers)

rename   (Rename a container)

restart  (Restart one or more containers)

rm       (Remove one or more containers)

run      (Create and run a new container from an image)

start    (Start one or more stopped containers)

stats    (Display a live stream of container(s) resource usage statistics)

stop     (Stop one or more running containers)

top      (Display the running processes of a container)

unpause  (Unpause all processes within one or more containers)

update   (Update configuration of one or more containers)

wait     (Block until one or more containers stop, then print their exit codes)


## Basic docker volume commands
```bash
sudo docker volume 
```

create   (Create a volume)

inspect  (Display detailed information on one or more volumes)

ls       (List volumes)

prune    (Remove unused local volumes)

rm       (Remove one or more volumes)

update   (Update a volume (cluster volumes only))


## Basic docker network commands
```bash
sudo docker network
```

connect     (Connect a container to a network)

create      (Create a network)

disconnect  (Disconnect a container from a network)

inspect     (Display detailed information on one or more networks)

ls          (List networks)

prune       (Remove all unused networks)

rm          (Remove one or more networks)


# Portainer

[https://www.portainer.io/](https://www.portainer.io/)

## Install Portainer within docker

[https://docs.portainer.io/start/install/server/docker/linux](https://docs.portainer.io/start/install/server/docker/linux)

This will walk your through creating and starting a portainer instance. Docker needs to be installed and working before this.



# Plex Media Server

You can run a plex media server from within Docker, the link will provide a git hub. You can amend the docker-compose to suit your needs.

## Plex Server Hub Link

[https://hub.docker.com/r/linuxserver/plex](https://hub.docker.com/r/linuxserver/plex)


# Next Cloud - Basic Install

This will cover getting a basic instance of NextCloud running. It will not include any Traefik configuration or CloudFlare DNS/SSL.

[https://nextcloud.com/blog/how-to-install-the-nextcloud-all-in-one-on-linux/](https://nextcloud.com/blog/how-to-install-the-nextcloud-all-in-one-on-linux/)


# Traefik - Reverse Proxy and Load Balancing

Recommended order for learning Traefik (but feel free to explore as you like!):

## Introduction:

[https://doc.traefik.io/traefik/](https://doc.traefik.io/traefik/)

## Concepts:

[https://doc.traefik.io/traefik/getting-started/concepts/](https://doc.traefik.io/traefik/getting-started/concepts/)

## FAQ:

[https://doc.traefik.io/traefik/getting-started/faq/](https://doc.traefik.io/traefik/getting-started/faq/)

## Configuration Overview:

[https://doc.traefik.io/traefik/getting-started/configuration-overview/](https://doc.traefik.io/traefik/getting-started/configuration-overview/)

## Providers Overview:

[https://doc.traefik.io/traefik/providers/overview/](https://doc.traefik.io/traefik/providers/overview/)

## Docker Provider:

[https://doc.traefik.io/traefik/providers/docker/](https://doc.traefik.io/traefik/providers/docker/)

## Quick Start Guide:

[https://doc.traefik.io/traefik/getting-started/quick-start/](https://doc.traefik.io/traefik/getting-started/quick-start/)