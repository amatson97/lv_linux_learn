# API Tokens & Credentials Guide

This guide explains how to obtain and use API tokens and credentials required by various scripts in this repository.

---

## 🔑 Overview

Several scripts require API tokens or credentials to function. This repository **never hardcodes tokens** for security. You must provide your own credentials through:

1. **Interactive prompts** (recommended for first-time use)
2. **Environment variables** (recommended for automation)
3. **Command-line arguments** (legacy support)

---

## 🌐 ZeroTier API Token

**Required by:**
- `zerotier_tools/zt_notifications.sh` - Network monitoring with desktop notifications
- `zerotier_tools/html_ip.sh` - HTML report of network members
- `zerotier_tools/get_ip.sh` - Simple IP listing

### How to Get Your Token

1. **Log in to ZeroTier Central**
   - Visit: https://my.zerotier.com/
   - Sign in with your account

2. **Navigate to API Access Tokens**
   - Click your profile icon (top-right corner)
   - Select **Account** from dropdown
   - Click **API Access Tokens** in the sidebar

3. **Generate New Token**
   - Click **Generate New Token**
   - Enter a name (e.g., "LV Linux Tools")
   - Click **Generate**
   - **Copy the token immediately** (you'll only see it once!)

4. **Token Format**
   - Alphanumeric string (typically 32+ characters)
   - Example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### How to Use

**Method 1: Interactive Prompt (Easiest)**
```bash
./zerotier_tools/zt_notifications.sh
# You'll be prompted for token and network ID
```

**Method 2: Environment Variable (Best for Scripts)**
```bash
export ZEROTIER_API_TOKEN="your_token_here"
export ZEROTIER_NETWORK_ID="your_network_id"
./zerotier_tools/zt_notifications.sh
```

**Method 3: Command Line Arguments**
```bash
./zerotier_tools/zt_notifications.sh YOUR_TOKEN YOUR_NETWORK_ID
```

### Security Notes
- ✅ Token grants **read-only** access to your networks
- ⚠️ Never commit tokens to git
- 🔄 Regenerate tokens periodically
- 🗑️ Revoke unused tokens at https://my.zerotier.com/

---

## 📡 ZeroTier Network ID

**Required by:**
- `scripts/new_vpn.sh` - ZeroTier VPN installation and setup
- `zerotier_tools/zt_notifications.sh` - Network monitoring
- `zerotier_tools/html_ip.sh` - HTML report generation
- `zerotier_tools/get_ip.sh` - IP listing

### How to Find Your Network ID

1. **Log in to ZeroTier Central**
   - Visit: https://my.zerotier.com/

2. **Select Your Network**
   - Click on the network you want to use
   - The network name is listed in your networks

3. **Copy the Network ID**
   - At the top of the network page
   - **16-character hexadecimal string**
   - Example: `8bd5124fd60a971f`

### Network ID Format
- Exactly **16 hexadecimal characters** (0-9, a-f)
- Case insensitive
- Uniquely identifies your private network

### How to Use

**Method 1: Environment Variable (Recommended)**
```bash
export ZEROTIER_NETWORK_ID="8bd5124fd60a971f"
./scripts/new_vpn.sh
```

**Method 2: Edit Script Directly**
```bash
# Edit scripts/new_vpn.sh
# Change line: readonly ZEROTIER_NETWORK=REPLACE_WITH_YOUR_NETWORK_ID
# To:          readonly ZEROTIER_NETWORK=8bd5124fd60a971f
```

**Method 3: Interactive Prompt**
```bash
./zerotier_tools/zt_notifications.sh
# You'll be prompted if network ID not set
```

---

## 🔐 NordVPN Access Token

**Required by:**
- `scripts/new_vpn.sh` - NordVPN installation and login
- Any script using `install_nord()` function from `includes/main.sh`

### How to Get Your Token

1. **Log in to NordVPN Account**
   - Visit: https://my.nordaccount.com/
   - Sign in with your credentials

2. **Navigate to Access Tokens**
   - Go to **Dashboard** → **NordVPN**
   - Click **Access Tokens** in sidebar
   - Direct link: https://my.nordaccount.com/dashboard/nordvpn/access-tokens/

3. **Generate New Token**
   - Click **Generate New Token**
   - Token will be displayed immediately
   - **Copy it** (cannot be viewed again)

4. **Token Format**
   - 64-character hexadecimal string
   - Example: `e9f2ab08980aa661ca66f5dd8c36ec865c809b28a2fef24646c9741e20c1cf81`

### How to Use

**Method 1: Interactive Prompt (Recommended)**
```bash
./scripts/new_vpn.sh
# You'll be prompted for NordVPN token when needed
```

**Method 2: Environment Variable**
```bash
export NORDVPN_TOKEN="your_token_here"
./scripts/new_vpn.sh
```

**Method 3: Direct Function Call**
```bash
source includes/main.sh
NORDVPN_TOKEN="your_token" install_nord
```

### Security Notes
- ⚠️ Token grants **full access** to your NordVPN account
- 🔒 Never commit tokens to git repositories
- 🔄 Regenerate if compromised
- 🗑️ Revoke old tokens when generating new ones

---

## 🐳 Docker Compose Environment Variables

**Required by:**
- `docker-compose/docker-compose.yml` - Various service configurations

### Setup

1. **Copy Example File**
   ```bash
   cp docker-compose/.env.example docker-compose/.env
   ```

2. **Edit with Your Values**
   ```bash
   nano docker-compose/.env
   ```

3. **Replace All Placeholders**
   - `YOURDOMAIN.COM` → Your actual domain
   - `YOURKEYHERE` → Your Cloudflare API token
   - `YOURPASSWORD` → Strong passwords
   - `yourkeyhere` → Your private keys

### Important Credentials

**Cloudflare DNS API Token:**
- Get at: https://dash.cloudflare.com/profile/api-tokens
- Permissions needed: Zone.DNS (Edit)

**Traefik Basic Auth:**
- Generate with: `htpasswd -nb username password`
- Format: `username:$apr1$hashed_password`

**Database Passwords:**
- Use strong, random passwords
- Generate with: `openssl rand -base64 32`

### Security Notes
- ⚠️ The `.env` file is gitignored (never commit it)
- 🔒 Store backup securely (password manager)
- 🔄 Rotate passwords periodically

---

## 📋 Quick Reference

| Script | Credentials Needed | How to Provide |
|--------|-------------------|----------------|
| `scripts/new_vpn.sh` | NordVPN Token, ZeroTier Network ID | Env vars or prompts |
| `zerotier_tools/zt_notifications.sh` | ZeroTier API Token, Network ID | Env vars, args, or prompts |
| `zerotier_tools/html_ip.sh` | ZeroTier API Token, Network ID | Env vars, args, or prompts |
| `zerotier_tools/get_ip.sh` | ZeroTier API Token, Network ID | Command line arguments |
| `docker-compose/*.yml` | Various (see .env.example) | Edit .env file |

---

## 🔐 Security Best Practices

### Do's ✅
- ✅ Use environment variables for automation
- ✅ Store tokens in password manager
- ✅ Rotate tokens/passwords regularly
- ✅ Use `.env` files (gitignored)
- ✅ Set minimal permissions for tokens
- ✅ Revoke unused/old tokens

### Don'ts ❌
- ❌ Commit tokens to git
- ❌ Share tokens in screenshots/logs
- ❌ Use same token across multiple machines
- ❌ Store tokens in plaintext files tracked by git
- ❌ Reuse passwords across services

---

## 🔧 Automation Example

Create a secure credential loader script:

```bash
#!/bin/bash
# ~/.lv_credentials.sh - Source this before running tools

# ZeroTier
export ZEROTIER_API_TOKEN="your_zerotier_token"
export ZEROTIER_NETWORK_ID="your_network_id"

# NordVPN
export NORDVPN_TOKEN="your_nordvpn_token"

# Make this file readable only by you
# chmod 600 ~/.lv_credentials.sh
```

**Usage:**
```bash
source ~/.lv_credentials.sh
./zerotier_tools/zt_notifications.sh  # No prompts needed!
```

⚠️ **Important:** Make sure `~/.lv_credentials.sh` is:
- Not in git repository
- Protected with `chmod 600`
- Listed in global `.gitignore_global`

---

## 🆘 Troubleshooting

### "No token provided" Error
- **Cause:** Token not set via any method
- **Fix:** Use interactive prompt, set env var, or pass as argument

### "Invalid token" Error
- **Cause:** Token expired, revoked, or incorrect
- **Fix:** Generate new token from service dashboard

### "Invalid network ID format"
- **Cause:** Network ID not 16 hex characters
- **Fix:** Copy exact ID from ZeroTier Central (e.g., `8bd5124fd60a971f`)

### "No response from API"
- **Cause:** Invalid token or network connectivity issue
- **Fix:** Check token validity, test internet connection

### Scripts Not Finding includes/main.sh
- **Cause:** Running from wrong directory
- **Fix:** Run from repository root: `./zerotier_tools/script.sh`

---

## 📞 Support

- **ZeroTier Help:** https://docs.zerotier.com/
- **NordVPN Support:** https://support.nordvpn.com/
- **Repository Issues:** https://github.com/amatson97/lv_linux_learn/issues

---

## 📜 License

This guide is part of the lv_linux_learn repository.  
See [LICENSE](../LICENSE) for details.
