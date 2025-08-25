# Perplexity API Response

## Prompt
```
Write me a docker-compose for a apache service running behind traefik.
- I already have a running and configured traefik instance, do not inlcude this in the compose.
- Configure the nesseary labels.
- it will site behind apache.ichigo1990.uk
- certresolver=cloudflare
- mount the following directory (/oldhome/apache)

```

## Response
Here is a Docker Compose configuration for an **Apache service** running behind 
an existing Traefik instance, with the necessary labels for routing, TLS, and 
Cloudflare certificate resolver. The Apache container mounts the directory 
**/oldhome/apache**.

```yaml
version: '3.8'

services:
  apache:
    image: httpd:latest
    container_name: apache
    volumes:
      - /oldhome/apache:/usr/local/apache2/htdocs/
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.apache.rule=Host(`apache.ichigo1990.uk`)"
      - "traefik.http.routers.apache.entrypoints=websecure"
      - "traefik.http.routers.apache.tls=true"
      - "traefik.http.routers.apache.tls.certresolver=cloudflare"
      - "traefik.http.services.apache.loadbalancer.server.port=80"
    networks:
      - traefik

networks:
  traefik:
    external: true
```

**Key points:**
- **Labels** configure Traefik to route HTTPS traffic for apache.ichigo1990.uk 
to this container, using the cloudflare certresolver[2][4].
- **EntryPoint** is set to websecure, which should match your Traefik HTTPS 
entrypoint name[2].
- **Volume** mounts /oldhome/apache to the Apache web root.
- **Network** assumes your Traefik instance uses an external Docker network 
named traefik. Adjust the network name if yours differs[2].
- **No Traefik service** is included, as you requested.

If your Apache container listens on a different internal port, adjust the 
loadbalancer.server.port label accordingly.

## Citations
- https://docs.vultr.com/set-up-traefik-proxy-as-a-reverse-proxy-for-docker-containers-on-ubuntu-24-04
- https://www.ssdnodes.com/blog/traefik-as-a-reverse-proxy-for-multiple-hosts-docker-compose/
- https://docs.docker.com/guides/traefik/
- https://doc.traefik.io/traefik/user-guides/docker-compose/basic-example/
- https://community.traefik.io/t/running-two-httpd-apache-behind-the-same-traeffik/5519
