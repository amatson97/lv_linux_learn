#!/bin/bash
# Auto-launcher for Setup Tool
# Detects environment and launches GUI or CLI version

# Check if we have a display server and Python GTK dependencies
if [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1; then
    # Try to import GTK - if successful, launch GUI
    if python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null; then
        exec python3 "$(dirname "$0")/menu.py" "$@"
    fi
fi

# Fall back to CLI menu
exec bash "$(dirname "$0")/menu.sh" "$@"
