# Linux Learning Guide
Support for Ubuntu Desktop 24.04.3 LTS

## Useful command reference for beginners:
[https://www.hostinger.com/tutorials/linux-commands]: https://www.hostinger.com/tutorials/linux-commands

# Install scripts
I have included some usefual automated install scripts.

## list of bash install scripts
```bash
install_remote_assist.sh
uninstall_remote_assist.sh
sublime_install.sh
sublime.merge_install.sh
chrome_install.sh
docker_install.sh
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
sudo chmod ./uninstall_remote_assist.sh
```
```bash
./uninstall_remote_assist.sh
```
# docker commands
Some basic docker commands for managing containers, volumes and networks. I will also look to putting in some docker-compose files for building services.

## basic docker-compose commands
```bash
docker compose up -d
docker compose down
```

## basic docker container commands
```bash
sudo docker container 

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
```

## basic docker volume commands
```bash
sudo docker volume 

create   (Create a volume)
inspect  (Display detailed information on one or more volumes)
ls       (List volumes)
prune    (Remove unused local volumes)
rm       (Remove one or more volumes)
update   (Update a volume (cluster volumes only))
```

## basic docker network commands
```bash
sudo docker network

connect     (Connect a container to a network)
create      (Create a network)
disconnect  (Disconnect a container from a network)
inspect     (Display detailed information on one or more networks)
ls          (List networks)
prune       (Remove all unused networks)
rm          (Remove one or more networks)
```

## Install Portainer within docker
[https://docs.portainer.io/start/install/server/docker/linux]: https://docs.portainer.io/start/install/server/docker/linux
This will walk your through creating and starting a portainer instance. Docker needs to be installed and working before this.