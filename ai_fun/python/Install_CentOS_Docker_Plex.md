# Perplexity API Response

## Prompt
Write me a guide to set up a CentOS server, install docker and set up a plex server.
## Response
To set up a **CentOS server**, install **Docker**, and deploy a **Plex Media Server** using Docker, follow these steps:

---

**1. Install CentOS**

- **Download the CentOS ISO** from the official website (choose the correct architecture, typically x86_64)[5].
- **Create a bootable USB/DVD** with the ISO.
- **Boot your server** from the installation media.
- At the welcome screen, choose *Install CentOS*.
- Select your preferred language and keyboard layout.
- Configure the network and set a hostname[3].
- Select the installation destination (disk/SSD)[1].
- Set the root password and create a user account[1][3].
- Begin the installation and reboot when complete[1][3][5].

---

**2. Install Docker on CentOS**

- Update your system:
  ```bash
  sudo yum update -y
  ```
- Install Docker:
  ```bash
  sudo yum install -y docker
  ```
- Start and enable Docker:
  ```bash
  sudo systemctl start docker
  sudo systemctl enable docker
  ```
- Add your user to the Docker group (to run Docker without sudo):
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```
- (Optional) Install Docker Compose if you want to use docker-compose:
  ```bash
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  ```

---

**3. Prepare Volumes for Plex**

- Create directories for Plex data:
  ```bash
  sudo mkdir -p /plex/database
  sudo mkdir -p /plex/transcode
  sudo mkdir -p /plex/media
  ```
- On RHEL-based systems (including CentOS), set SELinux to permissive mode for Plex to access these paths:
  ```bash
  sudo setenforce 0
  sudo sed -i 's/^SELINUX=.*/SELINUX=permissive/g' /etc/selinux/config
  ```
  This ensures Plex can read/write to the necessary folders[4].

---

**4. Deploy Plex Media Server with Docker**

- Run the Plex container (replace `<your-claim-token>` with your Plex claim token if you have one):
  ```bash
  docker run -d \
    --name plex \
    --network=host \
    -e PLEX_CLAIM=<your-claim-token> \
    -e TZ="America/New_York" \
    -v /plex/database:/config \
    -v /plex/transcode:/transcode \
    -v /plex/media:/data \
    plexinc/pms-docker
  ```
  - `--network=host` allows Plex to access your network directly.
  - `-v` flags map your host directories to the container for persistent storage[4].

- Wait for the container to start up. You can check its status:
  ```bash
  docker ps
  ```

---

**5. Access Plex Web Interface**

- Open a browser and navigate to `http://<your-server-ip>:32400/web`.
- Complete the Plex setup wizard and start adding your media.

---

**Additional Notes**

- If you want to use Docker Compose, you can create a `docker-compose.yml` file for Plex and run `docker-compose up -d`[4].
- Always use strong passwords for your root and Plex accounts.
- Make sure your server’s firewall allows traffic on Plex’s default port (32400).

---

This guide covers the essential steps for installing CentOS, setting up Docker, and running Plex Media Server in a Docker container, ensuring persistent storage and network access[1][3][4][5].
## Citations
- https://zap-hosting.com/guides/docs/dedicated-centos/
- https://www.rapidseedbox.com/blog/plex-on-docker
- https://www.webmo.net/support/centos72.html
- https://computingforgeeks.com/how-to-run-plex-media-server-in-docker-containers/
- https://www.geeksforgeeks.org/linux-unix/how-to-install-centos/

