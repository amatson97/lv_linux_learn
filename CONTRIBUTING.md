# Contributing to LV Linux Learn

First off, thank you for considering contributing to this project! 🎉

This repository helps Ubuntu Desktop users set up their development environments with interactive menus and automated scripts. Your contributions help make Linux more accessible.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Script Guidelines](#script-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct

This project follows a Code of Conduct. By participating, you agree to uphold a welcoming and inclusive environment. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 🚀 Getting Started

### Prerequisites

- Ubuntu Desktop 24.04.3 LTS (recommended)
- Basic bash scripting knowledge
- Git and GitHub CLI (`gh`)
- Python 3.10+ (for menu.py)
- jq (for manifest generation)

### Setup Development Environment

```bash
# Fork and clone
gh repo fork amatson97/lv_linux_learn --clone
cd lv_linux_learn

# Make scripts executable
chmod +x scripts/*.sh includes/*.sh tools/*.sh *.sh

# Test the menu
./menu.sh
```

### Repository Structure

```
lv_linux_learn/
├── scripts/          # Installation scripts (install category)
├── tools/            # Utility scripts (tools category)
├── bash_exercises/   # Learning exercises (exercises category)
├── uninstallers/     # Uninstaller scripts (uninstall category)
├── includes/         # Shared functions (main.sh)
├── zerotier_tools/   # ZeroTier VPN utilities
├── ai_fun/           # AI integration scripts
├── docs/             # Documentation
├── menu.sh           # CLI menu (bash)
├── menu.py           # GUI menu (Python/GTK)
├── manifest.json     # Script metadata (auto-generated)
└── .github/          # GitHub templates and workflows
```

## 🤝 How to Contribute

### Types of Contributions

1. **New Scripts**
   - Installation scripts (Docker, browsers, IDEs)
   - Utility tools (file conversion, system tools)
   - Learning exercises (bash tutorials)
   - Uninstallers (cleanup scripts)

2. **Bug Fixes**
   - Script errors or failures
   - Menu navigation issues
   - Manifest generation problems

3. **Documentation**
   - README improvements
   - Code comments
   - Usage guides in docs/

4. **Features**
   - Menu enhancements
   - New script categories
   - Search/filter improvements

### What We're Looking For

✅ **Good Contributions:**
- Ubuntu-focused scripts with clear use cases
- Idempotent installers (can run multiple times safely)
- Well-documented code with comments
- Scripts that follow existing patterns
- Security-conscious implementations

❌ **Please Avoid:**
- Scripts for other Linux distributions
- Production server configurations
- Hardcoded credentials or API keys
- Network-exposed services without warnings
- Breaking changes without discussion

### 🆘 **Areas Where We Need Help**

**High Priority - Infrastructure Improvements:**
- [ ] **CI/CD Pipeline Setup** - GitHub Actions for automated testing
  - Shellcheck validation for bash scripts
  - Python syntax checking for menu.py and AI tools
  - Documentation link validation
  - Manifest.json validation
- [ ] **Pre-commit Hooks** - Catch issues before commits
  - Integration with shellcheck, pylint, markdownlint
  - Secret scanning to prevent hardcoded credentials
- [ ] **Issue Templates** - Better structured bug reporting
  - Bug report template
  - Feature request template
  - Security issue template

**Medium Priority - Testing & Quality:**
- [ ] **Automated Testing Framework** - Replace manual VM testing
  - Integration tests for menu systems
  - Script execution validation
  - Docker-based testing environment
- [ ] **Code Quality Standards** - Consistent error handling
  - Standardized exit codes across scripts
  - Input validation helper functions
  - Error message consistency
- [ ] **Development Environment Guide** - Better contributor onboarding
  - Local testing setup with Docker/VM
  - Required tooling installation scripts
  - Troubleshooting common development issues

**Nice-to-Have - Community:**
- [ ] **Contributor Recognition** - Acknowledge community efforts
  - CONTRIBUTORS.md or all-contributors integration
  - Skill-level based contribution guidelines
  - Mentorship program for new contributors
- [ ] **Advanced Features** - Menu and script enhancements
  - Script search/filtering capabilities
  - Better error recovery in menu systems
  - Script dependency management

**💡 Want to tackle any of these?** Comment on related issues or create a new issue to discuss your approach!

## 🔧 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-new-script
```

Branch naming:
- `feature/` - New scripts or features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code improvements

### 2. Add Your Script

**Example: New Installation Script**

```bash
# Create script in appropriate directory
vim scripts/my_installer.sh

# Add script header
#!/bin/bash
# Description: Brief description of what this installs
# Author: Your Name
# Version: 1.0.0
# Requires: sudo, internet

set -euo pipefail

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../includes/main.sh"

green_echo "[*] Starting installation..."

# Your installation logic here

green_echo "[*] Installation complete!"
```

**Make executable:**
```bash
chmod +x scripts/my_installer.sh
```

### 3. Update Manifest

The manifest is auto-generated, but you should test it:

```bash
# Generate updated manifest
./scripts/generate_manifest.sh

# Check your script appears correctly
jq '.scripts[] | select(.id == "my-installer")' manifest.json
```

### 4. Test Thoroughly

```bash
# Test on fresh Ubuntu VM (recommended)
./menu.sh  # Verify script appears in menu
# Run your script
# Check for errors
# Test uninstaller (if applicable)
```

### 5. Document Changes

Update relevant docs:
- Add script to README.md (if major feature)
- Update docs/ files if needed
- Add inline comments explaining complex logic

## 📝 Script Guidelines

### Required Header Format

```bash
#!/bin/bash
# Description: What this script does (used in manifest.json)
# Author: Your Name (optional)
# Version: 1.0.0
# Requires: sudo, curl, specific-package
```

### Coding Standards

1. **Use strict mode:**
   ```bash
   set -euo pipefail
   ```

2. **Source shared helpers:**
   ```bash
   source includes/main.sh
   green_echo "[*] Status message"
   ```

3. **Validate input:**
   ```bash
   if [ -z "${MY_VAR:-}" ]; then
     echo "Error: MY_VAR not set"
     exit 1
   fi
   ```

4. **Quote variables:**
   ```bash
   install_package "$PACKAGE_NAME"  # Good
   install_package $PACKAGE_NAME    # Bad
   ```

5. **Check prerequisites:**
   ```bash
   if ! command -v docker &> /dev/null; then
     green_echo "[!] Docker not found. Installing..."
   fi
   ```

6. **Provide feedback:**
   ```bash
   green_echo "[*] Downloading package..."
   green_echo "[*] Installing..."
   green_echo "[*] Configuring..."
   green_echo "[✓] Done!"
   ```

### Security Requirements

- ✅ **Use environment variables for credentials**
- ✅ **Prompt user for sensitive input (don't hardcode)**
- ✅ **Validate network identifiers and tokens**
- ✅ **Document sudo requirements**
- ❌ **Never commit API keys or passwords**
- ❌ **Don't expose services to 0.0.0.0 without warning**

Example credential handling:
```bash
if [ -z "${API_KEY:-}" ]; then
  read -sp "Enter API key: " API_KEY
  echo
fi
```

### Idempotency Pattern

Scripts should be safe to run multiple times:

```bash
# Check if already installed
if command -v myapp &> /dev/null; then
  green_echo "[*] myapp already installed"
  myapp --version
  exit 0
fi

# Install only if not present
green_echo "[*] Installing myapp..."
sudo apt install -y myapp
```

## 🧪 Testing

### Manual Testing Checklist

**Current Process** (⚠️ **Help wanted: Let's automate this!**)

- [ ] Script runs without errors on Ubuntu 24.04.3 LTS
- [ ] Script appears in correct menu category
- [ ] Description is clear and accurate
- [ ] sudo prompts work correctly
- [ ] Script is idempotent (can run twice safely)
- [ ] Uninstaller works (if applicable)
- [ ] No hardcoded credentials
- [ ] Error messages are helpful

**💡 Automation Opportunities:**
- **CI/CD Pipeline:** Could automate syntax checking, shellcheck validation
- **Docker Testing:** Could spin up Ubuntu containers for testing
- **Integration Tests:** Could automate menu navigation and script execution
- **Security Scanning:** Could automatically detect hardcoded secrets

**Want to help build these automations?** This would be a **major contribution** to the project!

### Test on Fresh VM

**Recommended:** Test on a clean Ubuntu Desktop VM:

```bash
# VirtualBox or VMware with Ubuntu 24.04.3 LTS
# Clone repo
# Run your script
# Verify expected behavior
```

### Automated Tests

**Current Status:** Manual testing only - **This is a key area where we need contributor help!**

#### 🚀 **Automated Testing Opportunities (Contributors Welcome!)**

**1. CI/CD Pipeline Setup** (High Impact)
```yaml
# Needed: .github/workflows/test.yml
- Shellcheck for all *.sh files
- Python syntax validation
- Manifest.json schema validation
- Documentation link checking
- Security scanning (no hardcoded secrets)
```

**2. Pre-commit Hooks Integration**
```yaml
# Needed: .pre-commit-config.yaml
- shellcheck-py for bash validation
- python syntax checking
- markdownlint for documentation
- detect-secrets for credential scanning
```

**3. Integration Testing Framework**
```bash
# Ideas for implementation:
- Docker-based Ubuntu testing environment
- Menu navigation automation
- Script execution validation
- Cleanup verification (uninstallers)
```

**4. Current Manual Process** (What we want to automate)
- Test each script on Ubuntu 24.04.3 LTS VM
- Verify menu integration
- Check idempotency (run twice safely)
- Validate uninstallers
- Confirm no hardcoded secrets

**Want to help improve our testing?** Check existing issues tagged with `testing` or `ci-cd`, or create a new issue to discuss your approach!

## 📖 Documentation

### README Updates

For major features, add to README.md:
- Keep under 250 lines (detailed docs go in docs/)
- Update script count if needed
- Add to feature list if significant

### Inline Comments

Comment complex logic:

```bash
# Extract ZeroTier network ID from join output
# Format: "200 join OK" or error message
NETWORK_ID=$(zerotier-cli info | awk '{print $3}')
```

### docs/ Updates

Update topic-specific guides:
- `INSTALLATION.md` - New installers
- `TOOLS.md` - New utilities
- `DOCKER.md` - Docker-related changes
- `NETWORKING.md` - VPN/network changes

## 💬 Commit Messages

Follow conventional commits:

```
type(scope): Brief description

Longer explanation if needed.

- Bullet points for details
- Multiple changes listed
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code improvement
- `test:` - Testing changes
- `chore:` - Maintenance tasks

**Examples:**

```
feat(scripts): Add VSCode installer with extensions support

- Installs Microsoft Visual Studio Code
- Configures popular extensions
- Adds desktop launcher

Closes #42
```

```
fix(menu): Correct script count in Tools category

The display index was off by one due to custom scripts.
Fixed DISPLAY_TO_INDEX mapping logic.
```

```
docs: Update SECURITY.md with Docker considerations

Added section on Docker security implications and
privilege escalation concerns.
```

## 🔀 Pull Request Process

### Before Submitting

1. **Update manifest:**
   ```bash
   ./scripts/generate_manifest.sh
   ```

2. **Check for errors:**
   ```bash
   shellcheck scripts/my_script.sh
   bash -n scripts/my_script.sh  # Syntax check
   ```

3. **Clean commit history:**
   ```bash
   git rebase -i origin/main  # Squash commits if needed
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/my-new-script
   ```

### PR Template

Title: `feat: Add [Script Name] installer`

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] New script (installation, tool, exercise, uninstaller)
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested on Ubuntu 24.04.3 LTS
- [ ] Script is idempotent
- [ ] Appears correctly in menu
- [ ] No hardcoded secrets
- [ ] Uninstaller tested (if applicable)

## Screenshots (if applicable)
Menu screenshot showing new script.

## Checklist
- [ ] Followed script guidelines
- [ ] Added proper header with Description
- [ ] Used `set -euo pipefail`
- [ ] Sourced includes/main.sh
- [ ] Updated documentation
- [ ] Tested thoroughly
```

### Review Process

1. **Maintainer reviews within 7 days**
2. **Address feedback** with new commits or fixups
3. **Approval required** before merge
4. **Manifest auto-updates** on merge

### After Merge

- Your script will appear in manifest.json
- Both menus fetch updated list from GitHub
- Users get update within 1 hour (cache TTL)

## 🌟 Contributor Recognition

We believe in recognizing all contributors! Here's how we celebrate your contributions:

- **First-time contributors** get a warm welcome and guidance
- **Regular contributors** may be invited as collaborators
- **Significant improvements** (like CI/CD setup) will be highlighted in releases
- **All contributions** are tracked in git history and GitHub insights

### 📊 **Repository Contributor Readiness: 7/10**

**What This Means:**
- ✅ **Strong foundation** - Good documentation, security practices, code organization
- ⚠️ **Missing pieces** - Automated testing, streamlined onboarding, quality checks
- 🚀 **Your help can improve this score!** - CI/CD, testing, and process improvements needed

**Most Impactful Contributions Right Now:**
1. **GitHub Actions CI/CD setup** - Would dramatically improve code quality
2. **Pre-commit hooks integration** - Prevents issues before they're committed
3. **Testing framework** - Reduces manual validation burden
4. **Issue templates** - Improves bug reporting quality
5. **Development environment documentation** - Better contributor onboarding

## ❓ Questions?

- **General Questions:** Open a [GitHub issue](https://github.com/amatson97/lv_linux_learn/issues)
- **Feature Discussions:** Use [GitHub Discussions](https://github.com/amatson97/lv_linux_learn/discussions)
- **Security Issues:** See [SECURITY.md](SECURITY.md)
- **Want to Help with Infrastructure?** Look for issues tagged `help-wanted`, `good-first-issue`, or `infrastructure`

## 🎓 Learning Resources

- [Bash Scripting Guide](https://mywiki.wooledge.org/BashGuide)
- [Ubuntu Documentation](https://help.ubuntu.com/)
- [Shellcheck](https://www.shellcheck.net/) - Script linting
- [GitHub Flow](https://guides.github.com/introduction/flow/) - Workflow guide

---

**Thank you for contributing!** Your efforts help make Linux more accessible to everyone. 🐧✨
