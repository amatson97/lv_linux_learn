# Perplexity API Response

## Prompt
```
How would I configure a postgres database in centos with a whitelisted firewall
```
## Response
```
To configure a **PostgreSQL database on CentOS with a whitelisted firewall**, you need to (1) install and configure PostgreSQL, (2) configure the firewall to only allow trusted IPs, and (3) set PostgreSQL to accept connections only from those IPs.

**1. Install and Start PostgreSQL**
- Install PostgreSQL and initialize the database:
  ```bash
  sudo dnf install -y postgresql16-server
  sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
  sudo systemctl enable postgresql-16
  sudo systemctl start postgresql-16
  ```
- Create users and databases as needed[5].

**2. Configure the Firewall (firewalld)**
- Start and enable firewalld if not already running:
  ```bash
  sudo systemctl start firewalld
  sudo systemctl enable firewalld
  ```
- By default, you can open the PostgreSQL port (5432) to all:
  ```bash
  sudo firewall-cmd --add-service=postgresql --permanent
  sudo firewall-cmd --reload
  ```
- **To whitelist specific IPs only** (replace `X.X.X.X` with the allowed IP):
  ```bash
  sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="X.X.X.X" port protocol="tcp" port="5432" accept'
  ```
  Repeat for each IP you want to whitelist. Then reload the firewall:
  ```bash
  sudo firewall-cmd --reload
  ```
- You can verify the rules:
  ```bash
  sudo firewall-cmd --list-all
  ```
  This ensures only specified IPs can access PostgreSQL[1][3][5].

**3. Configure PostgreSQL for Remote Access**
- Edit `postgresql.conf` (location: `/var/lib/pgsql/<version>/data/postgresql.conf`) to listen on the appropriate interfaces:
  ```
  listen_addresses = 'localhost,X.X.X.X'
  ```
  Use a comma-separated list of IPs or `'0.0.0.0'` for all, but for security, specify only needed IPs[4][5].
- Edit `pg_hba.conf` (same directory) to allow connections only from whitelisted IPs:
  ```
  host    all    all    X.X.X.X/32    md5
  ```
  Add one line per allowed IP[4].

**4. Reload PostgreSQL**
- After editing configuration files, reload PostgreSQL:
  ```bash
  sudo systemctl reload postgresql-16
  ```

**Summary of Key Steps**
- **Install and start PostgreSQL**[5].
- **Whitelist IPs in firewalld** using rich rules[3][5].
- **Restrict PostgreSQL access** in `postgresql.conf` and `pg_hba.conf` to those IPs[4].
- **Reload/restart services** to apply changes[5].

This setup ensures only trusted, whitelisted IPs can connect to your PostgreSQL database on CentOS, providing a strong security baseline.
```## Citations
- https://keithmfoster.com/setting-up-replication-in-postgresql-11-centos-7/
- https://www.enterprisedb.com/blog/how-protect-your-postgresql-databases-cyberattacks-sql-firewall
- https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-using-firewalld-on-centos-7
- https://blog.devart.com/configure-postgresql-to-allow-remote-connection.html
- https://infotechys.com/install-and-configure-postgresql-on-rhel-9/

