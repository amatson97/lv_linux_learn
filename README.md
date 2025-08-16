# Linux Learning Guide

A guide to take your through installing remote assistance
Support for Ubuntu Desktop 24.04.3 LTS

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
## docker-compose.yml files
Provided some basic docker-compose.yml files for various services.

## basic docker-compose commands
```bash
docker compose up -d
docker compose down
```

## basic docker commands (containers)
```bash
sudo docker container ps
sudo docker container stop
sudo docker container restart
sudo docker container rm
```

## basic docker commands (volumes)
```bash
sudo docker volume create
sudo docker volume rm
sudo docker volume ls
sudo docker volume prune
```
