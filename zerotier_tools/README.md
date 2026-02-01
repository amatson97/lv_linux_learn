# ZeroTier Tools

This directory contains utility scripts for managing ZeroTier networking, a peer-to-peer VPN solution.

## Contents

### Network Utilities
- **get_ip.sh** - Get local ZeroTier IP address
- **html_ip.sh** - Generate HTML output with IP information
- **zt_notifications.sh** - ZeroTier status notifications

## Purpose

These scripts provide:
- **IP Management** - Query and retrieve ZeroTier IP addresses
- **Status Monitoring** - Monitor ZeroTier connection status
- **Web Integration** - Generate HTML output for web interfaces
- **Notifications** - Status alerts and notifications

## ZeroTier Overview

ZeroTier is a peer-to-peer VPN that:
- Creates virtual private networks
- Enables secure communication between devices
- Works across firewalls and NAT
- Requires no central server for operation

## Usage

### Get ZeroTier IP

```bash
./get_ip.sh
```

### Display IP as HTML

```bash
./html_ip.sh > network_status.html
```

### ZeroTier Status Notifications

```bash
./zt_notifications.sh
```

## Requirements

- ZeroTier installed (`sudo apt install zerotier-one`)
- Active ZeroTier network connection
- Bash shell

## Installation

```bash
# Install ZeroTier
sudo apt install zerotier-one

# Join a network
sudo zerotier-cli join <network_id>

# View network status
sudo zerotier-cli status
```

## Configuration

### Network ID

Each ZeroTier network has a unique 16-character hex ID:
```bash
# Find network ID
sudo zerotier-cli info
```

### Permissions

Most ZeroTier operations require root access:
```bash
sudo ./get_ip.sh
```

## Related Directories

- **../scripts/** - Installation scripts (includes VPN setup)
- **../tools/** - Other utility tools
- **../docs/guides/** - VPN and network setup guides

## Status

✅ Production Ready - Tested with ZeroTier node
