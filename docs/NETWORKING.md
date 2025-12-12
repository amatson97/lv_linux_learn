# Networking & VPN Guide

Complete guide for ZeroTier VPN, network tools, and remote access.

## Table of Contents
1. [ZeroTier Network Tools](#zerotier-network-tools)
2. [Automated Monitoring Setup](#automated-monitoring-setup)
3. [VPN Management](#vpn-management)

---

## ZeroTier Network Tools

The `zerotier_tools` directory contains utilities for managing and monitoring ZeroTier VPN networks.

### Available Scripts

```bash
# Get IP addresses of network members
./zerotier_tools/get_ip.sh <API_TOKEN> <NETWORK_ID>

# Generate HTML report of network status
./zerotier_tools/html_ip.sh <API_TOKEN> <NETWORK_ID>

# Desktop notifications for network changes
./zerotier_tools/zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

---

## Automated Monitoring Setup

Configure desktop notifications for network member status changes:

```bash
# Edit crontab
crontab -e

# Add this line (replace placeholders with actual values)
*/5 * * * * DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/<USER>/lv_linux_learn/zerotier_tools/zt_notifications.sh <API_TOKEN> <NETWORK_ID>
```

**What it does:**
- Checks every 5 minutes for network member status changes
- Issues desktop notifications when nodes come online/offline
- Shows member names and IP addresses

![ZeroTier Desktop Notifications](../images/zt_notifications.png "ZeroTier Desktop Notifications")

**Note:** Contact the repository administrator for `<API_TOKEN>` and `<NETWORK_ID>` values.

---

## VPN Management

### Uninstall All VPNs

Remove all VPN technologies from your machine:

```bash
./uninstallers/uninstall_all_vpn.sh
```

This removes:
- ZeroTier One
- NordVPN
- LogMeIn Hamachi

You can then disable remote desktop features in system settings.
