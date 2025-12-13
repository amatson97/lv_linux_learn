# Security Policy

## 🔒 Security Commitment

This repository contains Ubuntu Desktop setup and utility scripts. While designed for **localhost development environments only**, we take security seriously and welcome community feedback.

## ⚠️ Scope and Limitations

**Intended Use:**
- Ubuntu Desktop 24.04.3 LTS environments
- **Local development only** - not for production servers
- **Not hardened for public-facing services**
- Scripts assume trusted local network environment

**Out of Scope:**
- Production server deployments
- Internet-facing services
- Multi-user or multi-tenant environments
- Enterprise security compliance

## 🔐 Security Best Practices

### For Users

1. **Review Before Running**
   - Always read scripts before execution
   - Check `requires_sudo` flag in manifest.json
   - Scripts modify system configuration and install packages

2. **Credentials Management**
   - Never commit API keys, tokens, or passwords
   - Use environment variables for sensitive data:
     ```bash
     export PERPLEXITY_API_KEY="your_key_here"
     export NORDVPN_TOKEN="your_token_here"
     export ZEROTIER_NETWORK_ID="your_network_id"
     ```
   - Credentials stored in `~/.perplexity_api_key` should be chmod 600

3. **Network Security**
   - ZeroTier network IDs should be kept private
   - Docker containers expose ports only on localhost by default
   - Review firewall rules after VPN installations

4. **Script Permissions**
   - Scripts require sudo for system-level changes (apt, user groups)
   - Review what's installed: `./menu.sh` shows descriptions
   - Uninstallers provided for cleanup

### For Contributors

1. **No Hardcoded Secrets**
   - Never commit tokens, API keys, passwords, or private network IDs
   - Use prompts or environment variables for user credentials
   - Example: `prompt_zerotier_network()` in includes/main.sh

2. **Input Validation**
   - Validate user input before passing to shell commands
   - Use quotes around variables: `"$variable"`
   - Sanitize file paths and network identifiers

3. **Privilege Escalation**
   - Minimize sudo usage - request only when necessary
   - Document why sudo is required in script comments
   - Use `requires_sudo: true` in manifest.json

4. **Dependencies**
   - Pin critical package versions where possible
   - Verify package sources (official repos preferred)
   - Document external dependencies in script headers

5. **Code Review**
   - All PRs require review before merge
   - Security-sensitive changes need extra scrutiny
   - Test on fresh Ubuntu VM before submitting

## 🐛 Reporting a Vulnerability

### What to Report

- Hardcoded credentials or API keys
- Command injection vulnerabilities
- Privilege escalation beyond intended scope
- Malicious code or supply chain risks
- Exposed private network identifiers

### How to Report

**For Private/Critical Issues:**
1. **Do not open a public issue**
2. Email: [Create private security advisory on GitHub](https://github.com/amatson97/lv_linux_learn/security/advisories/new)
3. Include:
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

**For Non-Critical Issues:**
- Open a public issue with `[SECURITY]` prefix
- Provide sufficient detail for investigation
- Avoid posting sensitive data or exploits

### Response Timeline

| Severity | Initial Response | Fix Target |
|----------|-----------------|------------|
| Critical | 24 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 1 week | 30 days |
| Low | 2 weeks | Best effort |

## ✅ Security Checklist (Maintainers)

Before public release:
- [x] Remove all hardcoded credentials
- [x] Audit scripts for command injection
- [x] Review sudo usage patterns
- [x] Document credential management
- [x] Test installers on clean VM
- [x] Verify .gitignore excludes sensitive files
- [x] Check GitHub Actions workflow permissions
- [ ] Enable Dependabot security updates
- [ ] Enable GitHub code scanning
- [ ] Set up branch protection rules
- [ ] Configure required reviewers for PRs

## 🔍 Known Security Considerations

### Docker Installations
- Adds user to `docker` group (equivalent to root access)
- Docker daemon has significant system privileges
- Containers can access host network in some configurations

### VPN Installations
- Modifies system networking and routing tables
- May expose services to VPN network participants
- ZeroTier networks should use strong authentication

### WordPress Docker Compose
- Contains example passwords (`examplepass`, `somerootpassword`)
- **Must be changed before production use**
- Localhost-only by default (not exposed to internet)

### AI Integration
- Perplexity API key stored in `~/.perplexity_api_key`
- Key file should be chmod 600
- No API key validation before use

## 📚 Additional Resources

- [Ubuntu Security Guide](https://ubuntu.com/security)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Bash Security Pitfalls](https://mywiki.wooledge.org/BashPitfalls)

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-13 | 1.0.0 | Initial security policy for public repository |

---

**Last Updated:** December 13, 2025  
**Policy Version:** 1.0.0
