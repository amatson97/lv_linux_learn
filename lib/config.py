"""
Configuration values (renamed from constants.py)
Centralized configuration values, UI dimensions, and magic numbers
"""
from pathlib import Path
from typing import Final

# ============================================================================
# APPLICATION METADATA
# ============================================================================

APP_NAME: Final[str] = "LV Script Manager"
APP_VERSION: Final[str] = "2.1.0"
APP_ID: Final[str] = "com.lv.script_manager"
ARCHITECTURE_VERSION: Final[str] = "Multi-Repository System"

# ============================================================================
# PACKAGE REQUIREMENTS
# ============================================================================

REQUIRED_PACKAGES: Final[list[str]] = ["bash", "zenity", "sudo"]
OPTIONAL_PACKAGES: Final[list[str]] = ["bat", "pygmentize", "highlight"]
OPTIONAL_COMMANDS: Final[list[str]] = ["batcat", "pygmentize", "highlight"]

# ============================================================================
# MANIFEST & REPOSITORY CONFIGURATION
# ============================================================================

DEFAULT_MANIFEST_URL: Final[str] = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
MANIFEST_CACHE_MAX_AGE: Final[int] = 3600  # 1 hour in seconds
INCLUDES_CACHE_MAX_AGE: Final[int] = 86400  # 24 hours in seconds

# Force remote downloads (disable local repository detection)
FORCE_REMOTE_DOWNLOADS: Final[bool] = True  # Set to True to always download from GitHub

# Config directory structure
CONFIG_DIR: Final[Path] = Path.home() / '.lv_linux_learn'
MANIFEST_CACHE_FILE: Final[Path] = CONFIG_DIR / 'manifest.json'
UI_STATE_FILE: Final[Path] = CONFIG_DIR / 'ui_state.json'
CONFIG_FILE: Final[Path] = CONFIG_DIR / 'config.json'
CUSTOM_SCRIPTS_FILE: Final[Path] = CONFIG_DIR / 'custom_scripts.json'
SCRIPT_CACHE_DIR: Final[Path] = CONFIG_DIR / 'script_cache'

# ============================================================================
# UI DIMENSIONS & STYLING
# ============================================================================

# Window dimensions
DEFAULT_WINDOW_WIDTH: Final[int] = 996
DEFAULT_WINDOW_HEIGHT: Final[int] = 950
MIN_WINDOW_WIDTH: Final[int] = 800
MIN_WINDOW_HEIGHT: Final[int] = 600
DEFAULT_PANE_POSITION: Final[int] = 359

# Widget sizing
HEADER_SEARCH_WIDTH: Final[int] = 240
SCRIPT_LIST_MIN_WIDTH: Final[int] = 200
SCRIPT_LIST_MAX_WIDTH: Final[int] = 400
ICON_COLUMN_WIDTH: Final[int] = 30

# Spacing
WINDOW_BORDER_WIDTH: Final[int] = 12
TAB_BOX_SPACING: Final[int] = 16
TAB_BOX_BORDER: Final[int] = 12
BUTTON_BOX_SPACING: Final[int] = 8
CONTROL_BOX_SPACING: Final[int] = 5
WIDGET_MARGIN: Final[int] = 10

# Terminal
TERMINAL_SCROLLBACK_LINES: Final[int] = 10000

# ============================================================================
# GTK THEME COLORS (for reference/documentation)
# ============================================================================

# Header colors
HEADER_BG_START: Final[str] = "#2c3e50"
HEADER_BG_END: Final[str] = "#34495e"
HEADER_FG: Final[str] = "#ecf0f1"

# Terminal colors
TERMINAL_FG: Final[str] = "#EBEBEB"
TERMINAL_BG: Final[str] = "#1E1E1E"

# ============================================================================
# TREEVIEW COLUMN INDICES (Critical for avoiding index bugs!)
# ============================================================================

# Main script tabs column structure (7 columns)
COL_ICON: Final[int] = 0          # Cache status icon (✓/☁️)
COL_NAME: Final[int] = 1          # Display name
COL_PATH: Final[int] = 2          # Script path
COL_DESCRIPTION: Final[int] = 3   # Description text
COL_IS_CUSTOM: Final[int] = 4     # Custom script flag (bool)
COL_METADATA: Final[int] = 5      # Metadata JSON string
COL_SCRIPT_ID: Final[int] = 6     # Script ID

# Repository tab column structure (5 columns)
REPO_COL_SELECTED: Final[int] = 0     # Checkbox selection
REPO_COL_CACHED: Final[int] = 1       # Cache status icon
REPO_COL_NAME: Final[int] = 2         # Script name
REPO_COL_CATEGORY: Final[int] = 3     # Category
REPO_COL_DESCRIPTION: Final[int] = 4  # Description

# Local repository tab column structure (8 columns)
LOCAL_REPO_COL_SELECTED: Final[int] = 0  # Checkbox selection
LOCAL_REPO_COL_ID: Final[int] = 1        # Script ID
LOCAL_REPO_COL_NAME: Final[int] = 2      # Script name
LOCAL_REPO_COL_VERSION: Final[int] = 3   # Version
LOCAL_REPO_COL_PATH: Final[int] = 4      # File path
LOCAL_REPO_COL_CATEGORY: Final[int] = 5  # Category
LOCAL_REPO_COL_SOURCE: Final[int] = 6    # Source name
LOCAL_REPO_COL_SIZE: Final[int] = 7      # File size

# ============================================================================
# SCRIPT CATEGORIES
# ============================================================================

STANDARD_CATEGORIES: Final[list[str]] = ["install", "tools", "exercises", "uninstall"]
CATEGORY_ICONS: Final[dict[str, str]] = {
    "install": "📦",
    "tools": "🔧",
    "exercises": "📚",
    "uninstall": "⚠️",
    "repository": "📂",
}

# ============================================================================
# STATUS INDICATORS
# ============================================================================

ICON_CACHED: Final[str] = "✓"
ICON_NOT_CACHED: Final[str] = "☁️"
ICON_CUSTOM: Final[str] = "📝"
ICON_UPDATE_AVAILABLE: Final[str] = "🔄"

# ============================================================================
# SCRIPT SOURCE TYPES
# ============================================================================

SOURCE_TYPE_PUBLIC_REPO: Final[str] = "public_repo"
SOURCE_TYPE_CUSTOM_REPO: Final[str] = "custom_repo"
SOURCE_TYPE_CUSTOM_LOCAL: Final[str] = "custom_local"
SOURCE_TYPE_CUSTOM_SCRIPT: Final[str] = "custom_script"
SOURCE_TYPE_UNKNOWN: Final[str] = "unknown"

# Script execution types
SCRIPT_TYPE_LOCAL: Final[str] = "local"
SCRIPT_TYPE_CACHED: Final[str] = "cached"
SCRIPT_TYPE_REMOTE: Final[str] = "remote"

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_NO_MANIFESTS: Final[str] = "No manifests configured - enable public repository or add custom manifest"
ERROR_MANIFEST_LOAD_FAILED: Final[str] = "Failed to load any manifests"
ERROR_MISSING_PACKAGES: Final[str] = "Missing required packages"
ERROR_SCRIPT_NOT_FOUND: Final[str] = "Script file not found"
ERROR_CACHE_NOT_ENABLED: Final[str] = "Repository cache system not enabled"

# ============================================================================
# UI LABELS & TEXT
# ============================================================================

LABEL_TERMINAL_OUTPUT: Final[str] = "<b>Terminal Output</b>"
LABEL_SELECT_SCRIPT: Final[str] = "Select a script to see description."
LABEL_NO_DESCRIPTION: Final[str] = "No description available."

BUTTON_RUN: Final[str] = "Run Script in Terminal"
BUTTON_VIEW: Final[str] = "View Script"
BUTTON_GO_DIR: Final[str] = "Go to Directory"
BUTTON_CLEAR: Final[str] = "Clear"

# Menu items
MENU_FILE: Final[str] = "File"
MENU_REFRESH: Final[str] = "Refresh All Scripts"
MENU_QUIT: Final[str] = "Quit"
MENU_HELP: Final[str] = "Help"
MENU_ABOUT: Final[str] = "About"

# ============================================================================
# DIALOG MESSAGES
# ============================================================================

DIALOG_MISSING_PACKAGES_TITLE: Final[str] = "Missing Required Packages"
DIALOG_OPTIONAL_PACKAGES_TITLE: Final[str] = "Optional Packages Available"
DIALOG_DOWNLOAD_PROMPT_TITLE: Final[str] = "Download Script?"
DIALOG_CONFIRM_DELETE_TITLE: Final[str] = "Confirm Delete"
DIALOG_RESTART_REQUIRED_TITLE: Final[str] = "Restart Required"

# ============================================================================
# GITHUB & REPOSITORY URLS
# ============================================================================

GITHUB_REPO_URL: Final[str] = "https://github.com/amatson97/lv_linux_learn"
GITHUB_USER_URL: Final[str] = "https://github.com/amatson97"
GITHUB_RAW_BASE: Final[str] = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main"

# ============================================================================
# DESCRIPTION TEMPLATE SECTIONS (for About tab)
# ============================================================================

DESCRIPTION_TEMPLATE = {
    "app_name": "Linux Learning Setup Tool",
    "app_subtitle": "Advanced Ubuntu Linux Setup & Management Utility",
    "target_platform": "Ubuntu Desktop 24.04.3 LTS",
    "python_version": "Python 3.10+",
    "license": "MIT License",
    "developer": "Adam Matson",
}
