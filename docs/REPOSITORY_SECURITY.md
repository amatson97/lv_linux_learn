# Repository Security & Multi-Repository Setup Recommendations

This document provides GitHub repository security settings and configuration recommendations for both the main repository and custom repository creators using the multi-repository system.

## 🔐 Repository Security Settings

### Branch Protection Rules

Navigate to **Settings** → **Branches** → **Add rule** for `main` branch:

```yaml
Branch name pattern: main

Protection rules:
✅ Require a pull request before merging
  ✅ Require approvals: 1
  ✅ Dismiss stale PR approvals when new commits are pushed
  ✅ Require review from code owners
  
✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging
  
✅ Require conversation resolution before merging
✅ Require signed commits
✅ Include administrators (enforce for everyone)
✅ Restrict pushes that create files over 100MB
✅ Allow force pushes: ❌ Never
✅ Allow deletions: ❌ Never
```

### Security & Analysis

Navigate to **Settings** → **Security & analysis**:

> **Status Update (2025-12-13):** ✅ Dependabot security updates and GitHub code scanning are now **ACTIVE** on this repository.

```yaml
Private vulnerability reporting:
✅ Enable (allows private security advisories)

Dependency graph:
✅ Enable (tracks dependencies)

Dependabot alerts:
✅ Enable (security vulnerability notifications)

Dependabot security updates:
✅ **ENABLED** - Automatic security patches active

Code scanning alerts:
✅ **ENABLED** - CodeQL analysis monitoring for vulnerabilities
```

### Repository Access

Navigate to **Settings** → **Manage access**:

```yaml
Base permissions: Read
✅ Allow auto-merge
✅ Allow squash merging (recommended)
✅ Allow merge commits
✅ Allow rebase merging
✅ Auto-delete head branches after PR merge
✅ Always suggest updating pull request branches
```

## 🛡️ GitHub Actions Security

### Workflow Permissions

Navigate to **Settings** → **Actions** → **General**:

```yaml
Actions permissions:
○ Disable Actions (not recommended)
○ Allow enterprise and select non-enterprise actions
● Allow all actions and reusable workflows

Workflow permissions:
● Restricte (recommended for public repos)
  ✅ Read repository contents and packages permissions
  ❌ Write permissions (require explicit grants)
  
Fork pull request workflows:
● Require approval for first-time contributors
```

### Secrets Management

Navigate to **Settings** → **Secrets and variables** → **Actions**:

```yaml
Repository secrets: (if needed for future workflows)
- DEPLOY_TOKEN: (deployment token if automated deployment added)
- API_KEYS: (for external service integration)

Environment protection rules:
- production: Require reviewers before deployment
```

## 🔒 Security Monitoring

### Enable Security Features

1. **Private Security Advisories**
   - Settings → Security → Enable private vulnerability reporting
   - Allows researchers to report issues privately
   - Auto-creates CVE if needed

2. **Dependabot Configuration**
   ```yaml
   # .github/dependabot.yml (if adding dependencies)
   version: 2
   updates:
     - package-ecosystem: "github-actions"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

3. **CodeQL Analysis**
   - Settings → Security → Code scanning alerts → Set up CodeQL
   - Analyzes bash scripts for security issues
   - Runs on PR and push to main

## 📋 Community Health Files

Ensure these files exist in repository root:

```
├── SECURITY.md          ✅ Created
├── CONTRIBUTING.md      ✅ Created  
├── CODE_OF_CONDUCT.md   ✅ Created
├── LICENSE              ✅ Exists (MIT)
├── README.md            ✅ Updated for public repo
├── .github/
│   ├── ISSUE_TEMPLATE/  ✅ Created
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── security.yml
│   └── PULL_REQUEST_TEMPLATE/
│       └── pull_request_template.md ✅ Created
```

## ⚙️ Advanced Security Configuration

### Repository Topics

Navigate to **Settings** → **General** → **Topics**:

```
Suggested topics:
- ubuntu
- bash-scripts  
- linux-tools
- development-environment
- installer-scripts
- menu-system
- gtk
- python
- shell-scripting
- open-source
```

### Repository Description

```
Ubuntu Desktop setup and utility scripts with interactive CLI/GUI menus. 44+ curated scripts for development environment setup, tools, and learning exercises.
```

### Social Preview

Upload a repository social image:
- Recommended size: 1280×640px
- Include project logo/name
- Brief feature highlights

## 🔍 Security Audit Checklist

### Regular Security Tasks

- [ ] **Monthly**: Review Dependabot alerts
- [ ] **Quarterly**: Audit repository permissions
- [ ] **Bi-annually**: Review workflow permissions
- [ ] **On each release**: Security scan with CodeQL
- [ ] **Ongoing**: Monitor security advisories

### Script Security Review

Use this checklist for new scripts:

```bash
# Automated security checks
shellcheck scripts/*.sh tools/*.sh uninstallers/*.sh bash_exercises/*.sh

# Manual review points
- [ ] No hardcoded credentials
- [ ] Input validation present  
- [ ] Proper quoting of variables
- [ ] Sudo usage documented and minimal
- [ ] No eval() or dynamic code execution
- [ ] Network services bound to localhost only
- [ ] File permissions set appropriately
- [ ] Error handling prevents information disclosure
```

## 🌐 Multi-Repository Security Considerations

### Custom Repository Security Guidelines

When creating or using custom repositories with the multi-repository system:

#### Repository Creator Security

1. **Repository Access Control**
   ```yaml
   Repository visibility: 
   - Public: For open-source script libraries
   - Private: For organization-specific tools
   - Internal: For GitHub organization members only
   
   Access permissions:
   - Admin: Repository owners only
   - Write: Trusted contributors
   - Read: Users who need script access
   ```

2. **Script Content Security**
   ```bash
   # Security checklist for repository scripts:
   - [ ] No hardcoded credentials or tokens
   - [ ] All external URLs use HTTPS
   - [ ] Input validation for all parameters
   - [ ] Minimal sudo usage with clear documentation
   - [ ] No dynamic code execution (eval, etc.)
   - [ ] Proper error handling without information disclosure
   ```

3. **Manifest Security**
   ```json
   {
     "repository_url": "https://raw.githubusercontent.com/trusted-org/repo/main",
     "scripts": [{
       "checksum": "sha256:actual_hash_here",
       "requires_sudo": true,
       "tags": ["security-reviewed", "production-ready"]
     }]
   }
   ```

#### Repository User Security

1. **Repository Verification**
   ```bash
   # Before using a custom repository, verify:
   - Repository ownership and reputation
   - Recent activity and maintenance status
   - Security documentation and practices
   - Community feedback and reviews
   ```

2. **Configuration Security**
   ```bash
   # Custom repository configuration
   # Only use HTTPS URLs
   CUSTOM_MANIFEST_URL="https://raw.githubusercontent.com/trusted-org/repo/main/manifest.json"
   
   # Avoid insecure configurations
   # ❌ Never use: http://
   # ❌ Never use: file:// for remote configs
   # ❌ Never disable checksum verification
   ```

3. **Cache Security**
   ```bash
   # Regularly clear cache for untrusted repositories
   ./menu.sh -> Repository -> Clear Script Cache
   
   # Monitor cache contents
   ls -la ~/.lv_linux_learn/script_cache/
   
   # Review downloaded includes
   cat ~/.lv_linux_learn/script_cache/includes/main.sh
   ```

### Multi-Repository Threat Model

#### Threat: Malicious Custom Repository

- **Risk**: Attacker hosts malicious scripts in custom repository
- **Mitigation**: 
  - Repository verification before configuration
  - Checksum validation enabled (default)
  - User permission prompts for script downloads
  - Cache inspection capabilities

#### Threat: Compromised Repository

- **Risk**: Legitimate repository gets compromised with malicious updates
- **Mitigation**:
  - Checksum verification catches unauthorized changes
  - Manual update approval required
  - Repository activity monitoring
  - Rollback capabilities via cache clearing

#### Threat: Man-in-the-Middle Attacks

- **Risk**: Network interception of repository communications
- **Mitigation**:
  - HTTPS-only repository URLs enforced
  - Certificate validation required
  - No insecure HTTP allowed

#### Threat: Local Cache Tampering

- **Risk**: Local attacker modifies cached scripts
- **Mitigation**:
  - File permissions on cache directory
  - Checksum re-validation on execution
  - Cache integrity monitoring

### Security Best Practices for Multi-Repository Usage

#### For Repository Creators

1. **Implementation Security**
   ```bash
   # Use secure development practices
   # Enable branch protection rules
   # Require signed commits
   # Implement security scanning
   # Regular security audits
   ```

2. **Distribution Security**
   ```bash
   # Use official GitHub raw URLs
   # Maintain accurate checksums
   # Document security requirements
   # Provide security contact information
   ```

#### For Repository Users

1. **Due Diligence**
   ```bash
   # Research repository before use:
   # - Check GitHub repository directly
   # - Review commit history and contributors
   # - Look for security documentation
   # - Verify checksum accuracy
   ```

2. **Safe Configuration**
   ```bash
   # Test in isolated environment first
   # Use specific version tags when possible
   # Monitor for unexpected behavior
   # Regular security updates
   ```

#### For System Administrators

1. **Organizational Policy**
   ```bash
   # Approved repository whitelist
   # Security review process for new repositories
   # Incident response procedures
   # User training and awareness
   ```

2. **Monitoring and Auditing**
   ```bash
   # Log custom repository usage
   # Monitor script execution patterns
   # Regular cache content audits
   # Security compliance checks
   ```

### Multi-Repository Security Checklist

#### Repository Setup
- [ ] HTTPS-only repository URLs
- [ ] Accurate SHA256 checksums in manifest
- [ ] Security documentation provided
- [ ] Contact information for security reports
- [ ] Regular security updates and maintenance

#### User Configuration
- [ ] Repository verification completed
- [ ] Checksum verification enabled
- [ ] Cache monitoring implemented
- [ ] Incident response plan defined
- [ ] Regular security reviews scheduled

#### System Security
- [ ] File permissions configured correctly
- [ ] Network security policies enforced
- [ ] Logging and monitoring active
- [ ] Backup and recovery procedures tested
- [ ] Security training completed

## 🚨 Incident Response Plan

### Security Incident Response

1. **Critical Vulnerability Discovered**
   ```bash
   # Immediate actions
   1. Create private security advisory
   2. Develop and test fix
   3. Coordinate disclosure timeline
   4. Release security update
   5. Publish advisory with timeline
   ```

2. **Malicious Contribution Detected**
   ```bash
   # Response steps
   1. Immediately reject PR
   2. Block contributor if intentional
   3. Scan recent contributions from user
   4. Review related issues/PRs
   5. Update security policies if needed
   ```

3. **Credential Exposure**
   ```bash
   # Emergency response
   1. Immediately rotate exposed credentials
   2. Review git history for exposure scope
   3. Contact affected service providers
   4. Update security documentation
   5. Implement additional safeguards
   ```

## 📊 Security Metrics

Track these security indicators:

- **Dependabot alerts**: Target 0 open alerts
- **CodeQL findings**: Review and address all high/critical
- **PR review coverage**: 100% of security-sensitive changes
- **Time to patch**: <7 days for critical, <30 days for medium
- **Community engagement**: Active response to security reports

## 🔗 External Security Resources

- [GitHub Security Features](https://docs.github.com/en/code-security)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [CodeQL Analysis](https://docs.github.com/en/code-security/code-scanning)
- [Security Advisories](https://docs.github.com/en/code-security/security-advisories)
- [Bash Security Guide](https://mywiki.wooledge.org/BashPitfalls)

---

**Document Version:** 1.0.0  
**Last Updated:** December 13, 2025  
**Next Review:** March 2026