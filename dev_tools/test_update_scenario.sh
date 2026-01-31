#!/usr/bin/env bash
# Description: Set up a local test environment to verify script update detection without GitHub

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Test directories
TEST_ENV="${HOME}/.lv_linux_learn_test_env"
TEST_CACHE="${TEST_ENV}/script_cache"
TEST_MANIFESTS="${TEST_ENV}/manifests"
TEST_CONFIG="${TEST_ENV}/config.json"

# Colors for messages
print_header() {
    echo -e "${BLUE}▼▼▼ $1 ▼▼▼${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to create test scripts
create_test_scripts() {
    print_header "Creating Test Scripts"
    
    # Script 1: Docker Test (v1.0)
    mkdir -p "$TEST_MANIFESTS"
    
    cat > "$TEST_MANIFESTS/docker_test_v1.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Description: Test Docker installation script (v1.0)
set -euo pipefail

echo "=== Docker Test v1.0 ==="
echo "This is the OLD version - you should see an update available"
echo "Running basic checks..."
docker --version || echo "Docker not installed"
echo "Done!"
SCRIPT_EOF
    chmod +x "$TEST_MANIFESTS/docker_test_v1.sh"
    
    # Script 2: Git Setup Test (v1.0)
    cat > "$TEST_MANIFESTS/git_test_v1.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Description: Test Git configuration script (v1.0)
set -euo pipefail

echo "=== Git Test v1.0 ==="
echo "This is the OLD version - you should see an update available"
git --version || echo "Git not installed"
SCRIPT_EOF
    chmod +x "$TEST_MANIFESTS/git_test_v1.sh"
    
    # Script 3: Cleanup Test (v1.0)
    cat > "$TEST_MANIFESTS/cleanup_test_v1.sh" << 'SCRIPT_EOF'
#!/bin/bash
# Description: Test cleanup script (v1.0)
set -euo pipefail

echo "=== Cleanup Test v1.0 ==="
echo "This is the OLD version"
echo "Ready for cleanup"
SCRIPT_EOF
    chmod +x "$TEST_MANIFESTS/cleanup_test_v1.sh"
    
    print_success "Created test scripts in $TEST_MANIFESTS"
}

# Function to create test manifest
create_test_manifest() {
    print_header "Creating Test Manifest"
    
    # Calculate checksums for the OLD scripts
    DOCKER_SHA=$(sha256sum "$TEST_MANIFESTS/docker_test_v1.sh" | awk '{print $1}')
    GIT_SHA=$(sha256sum "$TEST_MANIFESTS/git_test_v1.sh" | awk '{print $1}')
    CLEANUP_SHA=$(sha256sum "$TEST_MANIFESTS/cleanup_test_v1.sh" | awk '{print $1}')
    
    # Create manifest with test scripts (these are the "remote" versions)
    # Using nested category structure: {"install": [...], "tools": [...]} with flat list
    cat > "$TEST_MANIFESTS/manifest.json" << MANIFEST_EOF
{
  "version": "1.0.0",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "repository": "Test Repository",
  "description": "Local test repository for update scenario testing",
  "scripts": {
    "install": [
      {
        "id": "docker_test",
        "name": "docker_test",
        "path": "file://$TEST_MANIFESTS/docker_test_v1.sh",
        "description": "Test Docker installation script (v1.0)",
        "checksum": "$DOCKER_SHA",
        "tags": ["docker", "test"]
      }
    ],
    "tools": [
      {
        "id": "git_test",
        "name": "git_test",
        "path": "file://$TEST_MANIFESTS/git_test_v1.sh",
        "description": "Test Git configuration script (v1.0)",
        "checksum": "$GIT_SHA",
        "tags": ["git", "test"]
      },
      {
        "id": "cleanup_test",
        "name": "cleanup_test",
        "path": "file://$TEST_MANIFESTS/cleanup_test_v1.sh",
        "description": "Test cleanup script (v1.0)",
        "checksum": "$CLEANUP_SHA",
        "tags": ["cleanup", "test"]
      }
    ]
  }
}
MANIFEST_EOF
    
    print_success "Created test manifest at $TEST_MANIFESTS/manifest.json"
    print_success "Manifest SHA256s calculated:"
    echo "  - docker_test: $DOCKER_SHA"
    echo "  - git_test: $GIT_SHA"
    echo "  - cleanup_test: $CLEANUP_SHA"
}

# Function to create outdated cache (simulating old cached scripts)
create_outdated_cache() {
    print_header "Creating Outdated Cache Versions"
    
    mkdir -p "$TEST_CACHE"
    
    # Create OLD (different) versions of scripts in cache
    # These have DIFFERENT content, so checksums won't match
    
    cat > "$TEST_CACHE/docker_test.sh" << 'CACHE_EOF'
#!/bin/bash
# Description: Test Docker installation script (v1.0)
# CACHED VERSION - OUTDATED - has different content
set -euo pipefail

echo "=== Docker Test (OLD CACHED VERSION) ==="
echo "This is the cached version which is OUTDATED"
echo "Server has a newer version available"
docker --version 2>/dev/null || echo "Docker not found"
CACHE_EOF
    chmod +x "$TEST_CACHE/docker_test.sh"
    
    cat > "$TEST_CACHE/git_test.sh" << 'CACHE_EOF'
#!/bin/bash
# Description: Test Git configuration script (v1.0)
# CACHED VERSION - OUTDATED
set -euo pipefail

echo "=== Git Test (OLD CACHED VERSION) ==="
echo "This is the cached version which is OUTDATED"
git --version 2>/dev/null || echo "Git not found"
CACHE_EOF
    chmod +x "$TEST_CACHE/git_test.sh"
    
    cat > "$TEST_CACHE/cleanup_test.sh" << 'CACHE_EOF'
#!/bin/bash
# Description: Test cleanup script (v1.0)
# CACHED VERSION - OUTDATED
set -euo pipefail

echo "=== Cleanup Test (OLD CACHED VERSION) ==="
echo "This is the cached version which is OUTDATED"
echo "Ready for cleanup"
CACHE_EOF
    chmod +x "$TEST_CACHE/cleanup_test.sh"
    
    print_success "Created outdated cache versions in $TEST_CACHE"
    print_success "These have DIFFERENT checksums than manifest, so update indicators should show"
}

# Function to create test config
create_test_config() {
    print_header "Creating Test Configuration"
    
    cat > "$TEST_CONFIG" << CONFIG_EOF
{
  "repositories": [
    {
      "name": "Test Repository",
      "manifest_url": "file://$TEST_MANIFESTS/manifest.json",
      "enabled": true,
      "description": "Local test repository for update scenario testing"
    }
  ],
  "cache_dir": "$TEST_CACHE",
  "settings": {
    "check_for_updates_interval": 60,
    "auto_download_updates": false
  }
}
CONFIG_EOF
    
    print_success "Created test config at $TEST_CONFIG"
}

# Function to verify checksums
verify_checksums() {
    print_header "Verifying Checksum Differences"
    
    echo "Remote (manifest) versions:"
    sha256sum "$TEST_MANIFESTS"/docker_test_v1.sh | awk '{print "  docker_test: " $1}'
    sha256sum "$TEST_MANIFESTS"/git_test_v1.sh | awk '{print "  git_test: " $1}'
    sha256sum "$TEST_MANIFESTS"/cleanup_test_v1.sh | awk '{print "  cleanup_test: " $1}'
    
    echo ""
    echo "Cached versions (DIFFERENT):"
    sha256sum "$TEST_CACHE"/docker_test.sh | awk '{print "  docker_test: " $1}'
    sha256sum "$TEST_CACHE"/git_test.sh | awk '{print "  git_test: " $1}'
    sha256sum "$TEST_CACHE"/cleanup_test.sh | awk '{print "  cleanup_test: " $1}'
}

# Function to show usage instructions
show_usage() {
    print_header "HOW TO TEST UPDATE DETECTION"
    
    cat << 'USAGE_EOF'
Now you have a complete test environment set up. To test update detection:

STEP 1: Update your config to use the test repository
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Option A: Via GUI (menu.py)
  1. Start menu.py: ./menu.py
  2. Go to Settings or Repository tab
  3. Add custom manifest: file:///home/adam/.lv_linux_learn_test_env/manifests/manifest.json
  4. Refresh/update manifest

Option B: Via config file (direct)
  Edit: ~/.lv_linux_learn/config.json
  Add this to repositories array:
  {
    "name": "Test Repository",
    "manifest_url": "file:///home/adam/.lv_linux_learn_test_env/manifests/manifest.json",
    "enabled": true
  }

STEP 2: Run the app
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./menu.py                    # GUI
  ./menu.sh                    # CLI

STEP 3: Verify update indicators
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You should see:
  ✓ 📥 indicator next to docker_test, git_test, cleanup_test
  ✓ Tab headers showing update count
  ✓ Update available in script info

The 📥 icon means: "update available" (cached version differs from remote)

STEP 4: Test download
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Click on docker_test with 📥 icon
  2. Select "Download" or "Update"
  3. Watch as it downloads the new version
  4. Verify checksum is now correct

STEP 5: Clean up when done
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Remove test environment
  rm -rf ~/.lv_linux_learn_test_env
  
  # Restore original config (if you modified it)
  # Or restart app to reset

TEST DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test manifest location:    /home/adam/.lv_linux_learn_test_env/manifests/manifest.json
Test cache location:       /home/adam/.lv_linux_learn_test_env/script_cache/
Test scripts location:     /home/adam/.lv_linux_learn_test_env/manifests/

The test scripts have DIFFERENT checksums in cache vs manifest,
so the app should detect them as needing updates.

USAGE_EOF
}

# Function to show cleanup instructions
show_cleanup() {
    print_header "CLEANUP INSTRUCTIONS"
    
    cat << 'CLEANUP_EOF'
To remove the test environment when done:

  rm -rf ~/.lv_linux_learn_test_env

If you modified your config file (~/.lv_linux_learn/config.json),
you may want to restore it to the original settings.

CLEANUP_EOF
}

# Main execution
main() {
    clear
    echo -e "${BLUE}"
    cat << 'BANNER_EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   LOCAL UPDATE SCENARIO TEST SETUP                            ║
║   Test script update detection without GitHub                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
BANNER_EOF
    echo -e "${NC}"
    
    # Check if already exists
    if [ -d "$TEST_ENV" ]; then
        print_warning "Test environment already exists at $TEST_ENV"
        read -p "Do you want to recreate it? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping existing environment"
            show_usage
            show_cleanup
            return 0
        fi
        rm -rf "$TEST_ENV"
        print_success "Removed existing environment"
    fi
    
    # Create everything
    create_test_scripts
    create_test_manifest
    create_outdated_cache
    create_test_config
    
    echo ""
    verify_checksums
    
    echo ""
    show_usage
    show_cleanup
    
    echo ""
    print_success "Test environment ready!"
    echo ""
}

main "$@"
