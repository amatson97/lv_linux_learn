# Troubleshooting Guide

Essential Linux troubleshooting techniques and tools.

## Table of Contents
1. [Common Command-Line Pitfalls](#common-command-line-pitfalls)
2. [Reading Log Files](#reading-log-files)
3. [System Resource Monitoring](#system-resource-monitoring)
4. [Network Troubleshooting](#network-troubleshooting)
5. [Additional Tips](#additional-tips)

---

## Common Command-Line Pitfalls

- **Misspelled commands** or options — use `command --help` to verify syntax
- **Permissions errors** — check file ownership and permissions with `ls -l`
- **Incorrect environment variables** — verify with `echo $VARIABLE_NAME`
- **Path issues** — confirm executable locations using `which <command>`

---

## Reading Log Files

System logs provide valuable insights into system behavior and errors:

```bash
# View system logs
sudo less /var/log/syslog

# Use journalctl for systemd-based logging
sudo journalctl -xe

# Check specific service logs (e.g., SSH)
sudo journalctl -u ssh

# Follow logs in real-time
sudo journalctl -f
```

### Application Logs (lv_linux_learn)

The application writes repository operation logs to a local file:

```bash
# View recent repository operations
tail -50 ~/.lv_linux_learn/logs/repository.log

# Clear the repository log
rm ~/.lv_linux_learn/logs/repository.log
```

Note: Verbose cache debug prints were removed in v2.2.3 to reduce noise. Use the repository log and the built-in test harness for troubleshooting.


## System Resource Monitoring

Monitor system health and resource usage:

- `top` — Interactive process viewer
- `htop` — Enhanced version of top (install with `sudo apt install htop`)
- `free -h` — Display memory usage
- `df -h` — Show disk space usage
- `du -sh <directory>` — Show size of a directory
- `ps aux` — List all running processes
- `kill <pid>` or `kill -9 <pid>` — Terminate a process by PID
- `lsof` — List open files (useful for finding which process is using a file)

---

## Network Troubleshooting

Diagnose connectivity and networking issues:

```bash
# Test network reachability
ping <hostname/ip>

# Trace the route packets take
traceroute <hostname>

# Show listening ports and connections
netstat -tuln
ss -tuln

# Check if a port is open
nc -zv <host> <port>

# Display IP addresses and interfaces
ip addr
ifconfig  # deprecated but still useful

# DNS lookup testing
nslookup <domain>
```

---

## Script Download & Cache Issues

### Checksum Verification Errors

If you see "checksum verification failed" errors when downloading scripts:

**What it means:**
- The downloaded script doesn't match the expected SHA256 checksum
- This usually indicates the script was updated but the manifest hasn't been regenerated yet
- It's a security feature to prevent corrupted or modified scripts from running

**Solutions:**
1. **Clear cache and retry:** Use "Clear Script Cache" in the Repository tab
2. **Wait for manifest update:** Contributors typically update the manifest within hours
3. **Check for local modifications:** Ensure you haven't modified scripts in the repository

**CLI Commands:**
```bash
# Clear cache manually
rm -rf ~/.lv_linux_learn/script_cache/

# Check script integrity
sha256sum scripts/example.sh
```

### Cache Management

- **Cache location:** `~/.lv_linux_learn/script_cache/`
- **Includes cache:** Automatically managed, refreshes every 24 hours
- **Manual cache clear:** Use Repository tab or delete cache directory

## Additional Tips

```bash
# View kernel messages (useful for hardware-related issues)
dmesg | less

# Restart services to apply changes or clear stuck states
sudo systemctl restart <service-name>
sudo systemctl status <service-name>

# Check disk usage when systems become slow
sudo du -h --max-depth=1 / | sort -hr
```

**When in doubt:** Search error messages online or check Linux community forums (see [Community Support](../README.md#-community-support))
