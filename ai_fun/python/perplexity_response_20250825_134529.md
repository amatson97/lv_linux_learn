# Perplexity API Response

## Prompt
```bash
Provide me a docker compose for a basic web server using apache.
```## Response
```
A basic Docker Compose file for an Apache web server uses the official **httpd** image and maps a local directory to the container for serving website files. Here is a minimal example:

```yaml
version: '3.9'
services:
  apache:
    image: httpd:latest
    container_name: my-apache-app
    ports:
      - '8080:80'
    volumes:
      - ./website:/usr/local/apache2/htdocs
```
This configuration will:
- Use the official **httpd:latest** image.
- Expose **port 80** in the container as **port 8080** on your host.
- Mount the local **./website** directory to the Apache document root, so files in `./website` will be served by Apache[3].

To run:
1. Place your website files (e.g., `index.html`) in the `./website` directory.
2. Save the above YAML as `docker-compose.yaml`.
3. Run `docker-compose up -d` in the same directory.

You can then access your web server at **http://localhost:8080**[3].
```## Citations
- https://www.digitalocean.com/community/tutorials/apache-web-server-dockerfile
- https://www.youtube.com/watch?v=-2qv1xh3CFs
- https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/Simple-Apache-docker-compose-example-with-Dockers-httpd-image
- https://www.docker.com/blog/how-to-use-the-apache-httpd-docker-official-image/
- https://forums.docker.com/t/setup-local-domain-and-ssl-for-php-apache-container/116015

