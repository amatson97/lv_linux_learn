#!/bin/bash
# Development tool to update manifest.json and push to GitHub
#
# DEVELOPMENT TOOL - Complete manifest update workflow
#
# Purpose:
#   - Regenerates manifest.json from current scripts
#   - Shows detailed diff of changes (added/removed/modified scripts)
#   - Provides interactive confirmation with safety checks
#   - Commits and pushes changes to GitHub with descriptive messages
#
# Usage:
#   ./dev_tools/update_manifest.sh
#
# Features:
#   - Automatic backup/restore on cancellation
#   - Change visualization (script counts, modifications)
#   - Optional full diff preview
#   - Descriptive commit messages
#
# Prerequisites:
#   - Git repository with push access
#   - jq installed (for JSON processing)
#   - Generated scripts via ./dev_tools/generate_manifest.sh

set -euo pipefail

# Colors
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
RED='\033[1;31m'
CYAN='\033[1;36m'
NC='\033[0m'

log() {
  echo -e "${GREEN}[*]${NC} $*"
}

info() {
  echo -e "${BLUE}[i]${NC} $*"
}

warn() {
  echo -e "${YELLOW}[!]${NC} $*"
}

error() {
  echo -e "${RED}[✗]${NC} $*"
}

success() {
  echo -e "${GREEN}[✓]${NC} $*"
}

# Get script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Backup current manifest
BACKUP_FILE="/tmp/manifest_backup_$(date +%s).json"
if [ -f "$REPO_ROOT/manifest.json" ]; then
  cp "$REPO_ROOT/manifest.json" "$BACKUP_FILE"
  info "Backed up current manifest to: $BACKUP_FILE"
fi

log "Updating manifest.json..."

# Generate new manifest
if [ -f "generate_manifest.sh" ]; then
  ./generate_manifest.sh
else
  error "Error: generate_manifest.sh not found in current directory"
  exit 1
fi

# Check if there are changes
if git -C "$REPO_ROOT" diff --quiet manifest.json 2>/dev/null; then
  success "No changes to manifest.json - already up to date!"
  rm -f "$BACKUP_FILE"
  exit 0
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    MANIFEST CHANGES DETECTED${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Analyze changes with jq
if command -v jq &> /dev/null && [ -f "$BACKUP_FILE" ]; then
  OLD_COUNT=$(jq '.scripts | length' "$BACKUP_FILE" 2>/dev/null || echo "0")
  NEW_COUNT=$(jq '.scripts | length' "$REPO_ROOT/manifest.json" 2>/dev/null || echo "0")
  
  echo -e "${BLUE}Script Count:${NC} $OLD_COUNT → $NEW_COUNT ($(($NEW_COUNT - $OLD_COUNT)))"
  echo ""
  
  # Get script names for comparison
  OLD_SCRIPTS=$(jq -r '.scripts[].id' "$BACKUP_FILE" 2>/dev/null | sort)
  NEW_SCRIPTS=$(jq -r '.scripts[].id' "$REPO_ROOT/manifest.json" 2>/dev/null | sort)
  
  # Find added scripts
  ADDED=$(comm -13 <(echo "$OLD_SCRIPTS") <(echo "$NEW_SCRIPTS"))
  if [ -n "$ADDED" ]; then
    echo -e "${GREEN}✚ Added Scripts:${NC}"
    while IFS= read -r script_id; do
      if [ -n "$script_id" ]; then
        script_name=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .name" "$REPO_ROOT/manifest.json" 2>/dev/null)
        script_path=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .relative_path" "$REPO_ROOT/manifest.json" 2>/dev/null)
        echo -e "  ${GREEN}+${NC} $script_name ($script_path)"
      fi
    done <<< "$ADDED"
    echo ""
  fi
  
  # Find removed scripts
  REMOVED=$(comm -23 <(echo "$OLD_SCRIPTS") <(echo "$NEW_SCRIPTS"))
  if [ -n "$REMOVED" ]; then
    echo -e "${RED}✗ Removed Scripts:${NC}"
    while IFS= read -r script_id; do
      if [ -n "$script_id" ]; then
        script_name=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .name" "$BACKUP_FILE" 2>/dev/null)
        script_path=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .relative_path" "$BACKUP_FILE" 2>/dev/null)
        echo -e "  ${RED}-${NC} $script_name ($script_path)"
      fi
    done <<< "$REMOVED"
    echo ""
  fi
  
  # Find modified scripts (checksum changes)
  COMMON=$(comm -12 <(echo "$OLD_SCRIPTS") <(echo "$NEW_SCRIPTS"))
  MODIFIED=""
  while IFS= read -r script_id; do
    if [ -n "$script_id" ]; then
      OLD_CHECKSUM=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .checksum" "$BACKUP_FILE" 2>/dev/null)
      NEW_CHECKSUM=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .checksum" "$REPO_ROOT/manifest.json" 2>/dev/null)
      if [ "$OLD_CHECKSUM" != "$NEW_CHECKSUM" ]; then
        MODIFIED="${MODIFIED}${script_id}\n"
      fi
    fi
  done <<< "$COMMON"
  
  if [ -n "$MODIFIED" ]; then
    echo -e "${YELLOW}✎ Modified Scripts (checksum changed):${NC}"
    echo -e "$MODIFIED" | while IFS= read -r script_id; do
      if [ -n "$script_id" ]; then
        script_name=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .name" "$REPO_ROOT/manifest.json" 2>/dev/null)
        script_path=$(jq -r ".scripts[] | select(.id == \"$script_id\") | .relative_path" "$REPO_ROOT/manifest.json" 2>/dev/null)
        echo -e "  ${YELLOW}~${NC} $script_name ($script_path)"
      fi
    done
    echo ""
  fi
  
  if [ -z "$ADDED" ] && [ -z "$REMOVED" ] && [ -z "$MODIFIED" ]; then
    info "Only metadata changed (timestamps, version, etc.)"
    echo ""
  fi
fi

# Show raw git diff stats
echo -e "${BLUE}Git Diff Summary:${NC}"
git -C "$REPO_ROOT" diff --stat manifest.json
echo ""

# Ask if user wants to see full diff
read -p "View full diff? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  git -C "$REPO_ROOT" diff --color=always manifest.json | less -R
  echo ""
fi

# Ask for confirmation
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
read -p "Commit and push manifest.json to GitHub? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  warn "Cancelled by user"
  # Restore backup
  if [ -f "$BACKUP_FILE" ]; then
    cp "$BACKUP_FILE" "$REPO_ROOT/manifest.json"
    info "Restored previous manifest from backup"
    rm -f "$BACKUP_FILE"
  fi
  exit 0
fi

# Clean up backup
rm -f "$BACKUP_FILE"

# Force add (despite gitignore) and commit
log "Committing manifest.json..."
git -C "$REPO_ROOT" add -f manifest.json

# Build commit message
COMMIT_MSG="chore: Update manifest.json"
if [ -n "${ADDED:-}" ]; then
  ADDED_COUNT=$(echo "$ADDED" | grep -c . || echo 0)
  COMMIT_MSG="${COMMIT_MSG}\n\n+ Added: $ADDED_COUNT script(s)"
fi
if [ -n "${REMOVED:-}" ]; then
  REMOVED_COUNT=$(echo "$REMOVED" | grep -c . || echo 0)
  COMMIT_MSG="${COMMIT_MSG}\n- Removed: $REMOVED_COUNT script(s)"
fi
if [ -n "${MODIFIED:-}" ]; then
  MODIFIED_COUNT=$(echo -e "$MODIFIED" | grep -c . || echo 0)
  COMMIT_MSG="${COMMIT_MSG}\n~ Modified: $MODIFIED_COUNT script(s)"
fi

git -C "$REPO_ROOT" commit -m "$(echo -e "$COMMIT_MSG")"

# Push to GitHub
log "Pushing to GitHub..."
git -C "$REPO_ROOT" push origin main

echo ""
success "✓ Manifest updated and pushed successfully!"
echo ""
info "GitHub users will receive the update within 1 hour (cache TTL)"
