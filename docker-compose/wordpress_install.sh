#!/bin/bash
# Example of a self contained install scrips.
# Installs all required packages, docker and sets up the docker compose file.
# It can be run on clean install VM to spin up a word press instance wthin docker.

# Update package list and install prerequisites
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Start Docker and enable it to start at boot
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Create project directory
PROJECT_DIR="$HOME/wordpress-docker"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create docker-compose.yml file
cat <<EOF > docker-compose.yml
version: '3.8'

services:
  wordpress:
    image: wordpress:latest
    ports:
      - "8000:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: exampleuser
      WORDPRESS_DB_PASSWORD: examplepass
      WORDPRESS_DB_NAME: exampledb
    volumes:
      - wordpress_data:/var/www/html

  db:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: somerootpassword
      MYSQL_DATABASE: exampledb
      MYSQL_USER: exampleuser
      MYSQL_PASSWORD: examplepass
    volumes:
      - db_data:/var/lib/mysql

volumes:
  wordpress_data:
  db_data:
EOF

# Start Docker containers
docker-compose up -d

# Output message with further instructions
echo "WordPress is being set up. Please wait a few moments."
echo "Once the setup is complete, you can access your WordPress site at http://localhost:8000"
echo "To stop the Docker containers, run 'docker-compose down' in the $PROJECT_DIR directory."