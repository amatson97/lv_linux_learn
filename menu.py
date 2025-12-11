#!/usr/bin/env python3
"""
Setup Tool - Ubuntu Linux Setup & Management Utility
Requires: python3-gi, gir1.2-gtk-3.0, gir1.2-vte-2.91
"""

import sys
import os

# Check for required Python GTK dependencies before importing
try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Vte", "2.91")
    from gi.repository import Gtk, Gdk, GLib, Vte
except (ImportError, ValueError) as e:
    print("ERROR: Missing required Python GTK dependencies!")
    print("\nThis application requires:")
    print("  • python3-gi")
    print("  • gir1.2-gtk-3.0")
    print("  • gir1.2-vte-2.91")
    print("\nInstall them with:")
    print("  sudo apt-get update")
    print("  sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91")
    print(f"\nError details: {e}")
    sys.exit(1)

import subprocess
import webbrowser
import shlex
from pathlib import Path
try:
    # optional nicer icons / pixbuf usage if available
    from gi.repository import GdkPixbuf
except Exception:
    GdkPixbuf = None

REQUIRED_PACKAGES = ["bash", "zenity", "sudo"]
# Note: bat is installed as 'batcat' on Ubuntu/Debian
OPTIONAL_PACKAGES = ["batcat", "pygmentize", "highlight"]  # For syntax highlighting in View Script

SCRIPTS = [
    "scripts/new_vpn.sh",
    "scripts/chrome_install.sh",
    "scripts/docker_install.sh",
    "scripts/git_setup.sh",
    "scripts/install_flatpak.sh",
    "scripts/sublime_install.sh",
    "scripts/install_wine.sh",
    "scripts/nextcloud_client.sh",
]

SCRIPT_NAMES = [
    "ZeroTier VPN",
    "Google Chrome",
    "Docker",
    "Git & GitHub CLI",
    "Flatpak & Flathub",
    "Sublime Text & Merge",
    "Wine & Winetricks",
    "Nextcloud Client",
]

TOOLS_SCRIPTS = [
    "tools/git_pull.sh",
    "tools/git_push_changes.sh",
    "tools/7z_extractor.sh",
    "tools/7z_extractor_ram_disk.sh",
    "tools/check_power_on_hours.sh",
    "tools/convert_7z_to_xiso.sh",
    "tools/extract_rar.sh",
    "tools/flac_to_mp3.sh",
    "tools/plex-batch-remux.sh",
    "tools/ubuntu_NetworkManager.sh",
    "tools/zip_extractor_ram_disk.sh",
]

TOOLS_NAMES = [
    "Git Pull Changes",
    "Git Push Changes",
    "Extract 7z Archives",
    "Extract 7z to RAM Disk",
    "Check Drive Power-On Hours",
    "Convert 7z to XISO",
    "Extract RAR Archives",
    "Convert FLAC to MP3",
    "Plex Batch Remux",
    "NetworkManager Setup",
    "Extract ZIP to RAM Disk",
]

EXERCISES_SCRIPTS = [
    "bash_exercises/hello_world.sh",
    "bash_exercises/show_date.sh",
    "bash_exercises/list_files.sh",
    "bash_exercises/make_directory.sh",
    "bash_exercises/print_numbers.sh",
    "bash_exercises/simple_calculator.sh",
    "bash_exercises/find_word.sh",
    "bash_exercises/count_lines.sh",
]

EXERCISES_NAMES = [
    "Hello World",
    "Show Date",
    "List Files",
    "Make Directory",
    "Print Numbers",
    "Simple Calculator",
    "Find Word",
    "Count Lines",
]

UNINSTALL_SCRIPTS = [
    "uninstallers/uninstall_zerotier.sh",
    "uninstallers/uninstall_nordvpn.sh",
    "uninstallers/uninstall_docker.sh",
    "uninstallers/uninstall_chrome.sh",
    "uninstallers/uninstall_sublime.sh",
    "uninstallers/uninstall_flatpak.sh",
    "uninstallers/uninstall_wine.sh",
    "uninstallers/uninstall_nextcloud.sh",
    "scripts/remove_all_vpn.sh",
    "uninstallers/uninstall_all_vpn.sh",
    "uninstallers/clean_desktop_launchers.sh",
]

UNINSTALL_NAMES = [
    "ZeroTier VPN",
    "NordVPN",
    "Docker",
    "Google Chrome",
    "Sublime Text",
    "Flatpak",
    "Wine",
    "Nextcloud Client",
    "All VPN Clients (Legacy)",
    "All VPN Tools",
    "Desktop Launchers Only",
]

DESCRIPTIONS = [
    "<b>Install ZeroTier VPN</b>\n"
    "Script: <tt>scripts/new_vpn.sh</tt>\n\n"
    "• Joins the Linux Learn Network using ZeroTier, a flexible virtual network.\n"
    "• Removes conflicting VPN clients automatically.\n"
    "• Provides secure peer-to-peer virtual networking.\n\n"
    "More info:\n"
    "  • <a href='https://www.zerotier.com/'>ZeroTier Official Site</a>\n",

    "<b>Install Google Chrome</b>\n"
    "Script: <tt>scripts/chrome_install.sh</tt>\n\n"
    "• Adds official Google repository and keys to install stable Chrome.\n"
    "• Ensures latest browser improvements and security.\n\n"
    "Visit:\n"
    "  • <a href='https://www.google.com/chrome/'>Google Chrome Official</a>",

    "<b>Install Docker</b>\n"
    "Script: <tt>scripts/docker_install.sh</tt>\n\n"
    "• Installs Docker Engine, CLI, containerd, and plugins on Ubuntu.\n"
    "• Supports container management and orchestration.\n\n"
    "Docs:\n"
    "  • <a href='https://docs.docker.com/engine/install/ubuntu/'>Official Docker Install Guide</a>",

    "<b>Setup Git &amp; GitHub CLI</b>\n"
    "Script: <tt>scripts/git_setup.sh</tt>\n\n"
    "• Configures Git with user details.\n"
    "• Authenticates GitHub CLI for repository management.\n\n"
    "Learn more:\n"
    "  • <a href='https://cli.github.com/manual/'>GitHub CLI Manual</a>\n"
    "  • <a href='https://git-scm.com/doc'>Git Official Docs</a>",

    "<b>Install Flatpak &amp; Flathub</b>\n"
    "Script: <tt>scripts/install_flatpak.sh</tt>\n\n"
    "• Sets up Flatpak package manager.\n"
    "• Adds Flathub repository for universal Linux apps.\n\n"
    "Find out:\n"
    "  • <a href='https://flatpak.org/'>Flatpak Official Site</a>",

    "<b>Install Sublime Text &amp; Merge</b>\n"
    "Script: <tt>scripts/sublime_install.sh</tt>\n\n"
    "• Installs Sublime Text editor and Sublime Merge Git client.\n"
    "• Features GPU rendering, context-aware autocomplete, refreshed UI.\n\n"
    "Explore:\n"
    "  • <a href='https://www.sublimetext.com/'>Sublime Text</a>\n"
    "  • <a href='https://www.sublimemerge.com/'>Sublime Merge</a>",

    "<b>Install Wine &amp; Winetricks</b>\n"
    "Script: <tt>scripts/install_wine.sh</tt>\n\n"
    "• Installs Wine compatibility layer and Winetricks scripts.\n"
    "• Includes Microsoft Visual C++ 4.2 runtime setup.\n\n"
    "More info:\n"
    "  • <a href='https://wiki.winehq.org/Winetricks'>Winetricks Wiki</a>\n"
    "  • <a href='https://www.winehq.org/'>WineHQ</a>",

    "<b>Install Nextcloud Desktop Client</b>\n"
    "Script: <tt>scripts/nextcloud_client.sh</tt>\n\n"
    "• Installs Nextcloud sync client via Flatpak.\n"
    "• Supports personal and enterprise Nextcloud servers.\n\n"
    "More reading:\n"
    "  • <a href='https://nextcloud.com/install/#install-clients'>Nextcloud Install Clients</a>\n"
    "  • <a href='https://docs.nextcloud.com/'>Nextcloud Documentation</a>",
]

TOOLS_DESCRIPTIONS = [
    "<b>Git Pull Changes</b>\n"
    "Script: <tt>tools/git_pull.sh</tt>\n\n"
    "• Pulls latest changes from remote repositories.\n"
    "• Updates your local repository with changes from GitHub.\n\n"
    "Details:\n"
    "  • <a href='https://git-scm.com/docs/git-pull'>Git Pull Documentation</a>",

    "<b>Git Push Changes</b>\n"
    "Script: <tt>tools/git_push_changes.sh</tt>\n\n"
    "• Stages, commits, and pushes local changes to remote repo.\n"
    "• Interactive workflow for committing your work.\n\n"
    "Learn:\n"
    "  • <a href='https://git-scm.com/docs/git-push'>Git Push Documentation</a>",

    "<b>Extract 7z Archives</b>\n"
    "Script: <tt>tools/7z_extractor.sh</tt>\n\n"
    "• Extracts all .7z files in the current directory.\n"
    "• Removes original archives after successful extraction.\n"
    "• Useful for batch extraction of compressed files.",

    "<b>Extract 7z to RAM Disk</b>\n"
    "Script: <tt>tools/7z_extractor_ram_disk.sh</tt>\n\n"
    "• Extracts 7z archives to a RAM disk for faster processing.\n"
    "• Creates temporary RAM disk mount point.\n"
    "• Ideal for working with large archives on systems with plenty of RAM.",

    "<b>Check Drive Power-On Hours</b>\n"
    "Script: <tt>tools/check_power_on_hours.sh</tt>\n\n"
    "• Checks SMART data for multiple drives.\n"
    "• Reports power-on hours and health status.\n"
    "• Useful for monitoring drive health and lifespan.",

    "<b>Convert 7z to XISO</b>\n"
    "Script: <tt>tools/convert_7z_to_xiso.sh</tt>\n\n"
    "• Converts 7z compressed Xbox ISO images to XISO format.\n"
    "• Extracts and repackages for Xbox compatibility.\n"
    "• Uses extract-xiso tool for proper formatting.",

    "<b>Extract RAR Archives</b>\n"
    "Script: <tt>tools/extract_rar.sh</tt>\n\n"
    "• Extracts all .rar files in the current directory.\n"
    "• Handles multi-part RAR archives.\n"
    "• Removes originals after successful extraction.",

    "<b>Convert FLAC to MP3</b>\n"
    "Script: <tt>tools/flac_to_mp3.sh</tt>\n\n"
    "• Converts FLAC audio files to MP3 format.\n"
    "• Uses ffmpeg for high-quality conversion.\n"
    "• Configurable bitrate (default 192k).",

    "<b>Plex Batch Remux</b>\n"
    "Script: <tt>tools/plex-batch-remux.sh</tt>\n\n"
    "• Batch remux video files for Plex compatibility.\n"
    "• Fixes container issues without re-encoding.\n"
    "• Processes multiple files automatically.",

    "<b>NetworkManager Setup</b>\n"
    "Script: <tt>tools/ubuntu_NetworkManager.sh</tt>\n\n"
    "• Configures NetworkManager on Ubuntu.\n"
    "• Fixes network configuration issues.\n"
    "• Useful for troubleshooting network connectivity.",

    "<b>Extract ZIP to RAM Disk</b>\n"
    "Script: <tt>tools/zip_extractor_ram_disk.sh</tt>\n\n"
    "• Extracts ZIP archives to a RAM disk.\n"
    "• Creates temporary RAM disk for faster extraction.\n"
    "• Ideal for large archives on systems with sufficient RAM.",
]

EXERCISES_DESCRIPTIONS = [
    "<b>Hello World</b>\n"
    "Script: <tt>bash_exercises/hello_world.sh</tt>\n\n"
    "• Classic first program - prints 'Hello, World!'\n"
    "• Demonstrates basic bash script structure.\n"
    "• Perfect starting point for learning bash.",

    "<b>Show Date</b>\n"
    "Script: <tt>bash_exercises/show_date.sh</tt>\n\n"
    "• Displays current date and time.\n"
    "• Shows how to use the date command.\n"
    "• Learn basic command execution in scripts.",

    "<b>List Files</b>\n"
    "Script: <tt>bash_exercises/list_files.sh</tt>\n\n"
    "• Lists files in the current directory.\n"
    "• Demonstrates the ls command.\n"
    "• Practice working with directory listings.",

    "<b>Make Directory</b>\n"
    "Script: <tt>bash_exercises/make_directory.sh</tt>\n\n"
    "• Creates a new directory.\n"
    "• Shows user input with read command.\n"
    "• Learn directory creation and user interaction.",

    "<b>Print Numbers</b>\n"
    "Script: <tt>bash_exercises/print_numbers.sh</tt>\n\n"
    "• Prints numbers from 1 to 10.\n"
    "• Demonstrates for loop usage.\n"
    "• Practice basic iteration in bash.",

    "<b>Simple Calculator</b>\n"
    "Script: <tt>bash_exercises/simple_calculator.sh</tt>\n\n"
    "• Adds two numbers entered by user.\n"
    "• Shows arithmetic operations in bash.\n"
    "• Learn user input and mathematical operations.",

    "<b>Find Word</b>\n"
    "Script: <tt>bash_exercises/find_word.sh</tt>\n\n"
    "• Searches for a word in a file.\n"
    "• Demonstrates grep command usage.\n"
    "• Practice text searching and pattern matching.",

    "<b>Count Lines</b>\n"
    "Script: <tt>bash_exercises/count_lines.sh</tt>\n\n"
    "• Counts lines in a file.\n"
    "• Shows file testing and wc command.\n"
    "• Learn conditional logic and file operations.",
]

UNINSTALL_DESCRIPTIONS = [
    "<b>⚠️ Uninstall ZeroTier VPN</b>\n"
    "Script: <tt>uninstallers/uninstall_zerotier.sh</tt>\n\n"
    "• Leaves all ZeroTier networks before removal.\n"
    "• Removes ZeroTier package and configurations.\n"
    "• Cleans up sudoers file and desktop icons.",

    "<b>⚠️ Uninstall NordVPN</b>\n"
    "Script: <tt>uninstallers/uninstall_nordvpn.sh</tt>\n\n"
    "• Disconnects active VPN connection.\n"
    "• Disables Meshnet and logs out.\n"
    "• Removes user from nordvpn group.\n"
    "• Cleans up repository and desktop icons.",

    "<b>⚠️ Uninstall Docker</b>\n"
    "Script: <tt>uninstallers/uninstall_docker.sh</tt>\n\n"
    "• <b>WARNING:</b> Removes all containers, images, volumes, and networks.\n"
    "• Stops Docker service and removes packages.\n"
    "• Cleans up Docker data directories.\n"
    "• Removes user from docker group.",

    "<b>⚠️ Uninstall Google Chrome</b>\n"
    "Script: <tt>uninstallers/uninstall_chrome.sh</tt>\n\n"
    "• Removes Chrome package and repository.\n"
    "• Optionally removes user data and cache.\n"
    "• Prompts before deleting personal data.",

    "<b>⚠️ Uninstall Sublime Text</b>\n"
    "Script: <tt>uninstallers/uninstall_sublime.sh</tt>\n\n"
    "• Removes Sublime Text and Sublime Merge.\n"
    "• Optionally removes user configuration.\n"
    "• Cleans up repository and GPG keys.",

    "<b>⚠️ Uninstall Flatpak</b>\n"
    "Script: <tt>uninstallers/uninstall_flatpak.sh</tt>\n\n"
    "• Lists all installed Flatpak applications.\n"
    "• Optionally removes all Flatpak apps.\n"
    "• Removes Flatpak package and data directories.",

    "<b>⚠️ Uninstall Wine</b>\n"
    "Script: <tt>uninstallers/uninstall_wine.sh</tt>\n\n"
    "• Removes Wine and Winetricks packages.\n"
    "• Optionally removes Wine prefix (~/.wine).\n"
    "• Cleans up Wine repository configurations.",

    "<b>⚠️ Uninstall Nextcloud Client</b>\n"
    "Script: <tt>uninstallers/uninstall_nextcloud.sh</tt>\n\n"
    "• Removes Nextcloud Desktop client.\n"
    "• Optionally removes user configuration.\n"
    "• Cleans up sync data and cache.",

    "<b>⚠️ Remove All VPN Clients (Legacy)</b>\n"
    "Script: <tt>scripts/remove_all_vpn.sh</tt>\n\n"
    "• Original script to remove ZeroTier, NordVPN, and Hamachi.\n"
    "• Use 'Uninstall All VPN Tools' for newer implementation.",

    "<b>⚠️ Uninstall All VPN Tools</b>\n"
    "Script: <tt>uninstallers/uninstall_all_vpn.sh</tt>\n\n"
    "• Removes ZeroTier, NordVPN, and LogMeIn Hamachi.\n"
    "• Comprehensive cleanup of all VPN configurations.\n"
    "• Recommended over legacy script.",

    "<b>⚠️ Clean Desktop Launchers</b>\n"
    "Script: <tt>uninstallers/clean_desktop_launchers.sh</tt>\n\n"
    "• Removes all desktop icons created by install scripts.\n"
    "• Cleans up ~/.lv_connect helper scripts.\n"
    "• Does NOT uninstall applications, only launchers.",
]

DARK_CSS = b"""
window {
    background-color: #232629;
    color: #ebebeb;
    font-family: 'Ubuntu', 'Cantarell', 'Arial', sans-serif;
    font-size: 15px;
    border-radius: 8px;
    padding: 12px;
}

headerbar {
    min-height: 40px;
    padding: 0 6px;
}

button, .suggested-action {
    border-radius: 6px;
    background: #2f3640;
    color: #ebebeb;
    padding: 8px 14px;
    min-height: 34px;
    min-width: 96px;
    font-size: 14px;
}

button:hover, .suggested-action:hover {
    background: #3b4752;
}

#desc_label {
    margin-top: 8px;
    margin-bottom: 12px;
    font-style: italic;
    color: #ADB5BD;
    font-size: 13px;
}

.treeview {
    background: #1E1E1E;
    color: #ebebeb;
    border-radius: 6px;
    font-size: 14px;
}

/* selection highlight */
treeview treeview:selected, treeview:selected {
    background-color: #2a9d8f;
    color: #ffffff;
}

.scroll {
    border-radius: 6px;
    background: #1E1E1E;
    box-shadow: 1px 1px 6px rgba(0, 0, 0, 0.6);
}
"""

class ScriptMenuGTK(Gtk.ApplicationWindow):
    def __init__(self, app):
        # Use ApplicationWindow so GNOME/WM can associate the window with the Gtk.Application.
        Gtk.ApplicationWindow.__init__(self, application=app, title="Setup Tool")
        self.set_default_size(1200, 800)
        self.set_border_width(12)
        self.set_resizable(True)

        # HeaderBar + integrated search (keeps GNOME decoration/behavior consistent)
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Setup Tool"
        self.set_titlebar(hb)
        # add a small search entry to the headerbar for quick filtering
        self.header_search = Gtk.SearchEntry()
        self.header_search.set_placeholder_text("Search scripts...")
        self.header_search.set_size_request(240, -1)
        hb.pack_end(self.header_search)

        # Main container - vertical split
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_paned)

        # Top section - tabs
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Create notebook (tabs)
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        top_box.pack_start(self.notebook, True, True, 0)

        # Create Install tab
        install_box = self._create_script_tab(SCRIPTS, DESCRIPTIONS, "install")
        install_label = Gtk.Label(label="📦 Install")
        self.notebook.append_page(install_box, install_label)

        # Create Tools tab
        tools_box = self._create_script_tab(TOOLS_SCRIPTS, TOOLS_DESCRIPTIONS, "tools")
        tools_label = Gtk.Label(label="🔧 Tools")
        self.notebook.append_page(tools_box, tools_label)

        # Create Exercises tab
        exercises_box = self._create_script_tab(EXERCISES_SCRIPTS, EXERCISES_DESCRIPTIONS, "exercises")
        exercises_label = Gtk.Label(label="📚 Exercises")
        self.notebook.append_page(exercises_box, exercises_label)

        # Create Uninstall tab
        uninstall_box = self._create_script_tab(UNINSTALL_SCRIPTS, UNINSTALL_DESCRIPTIONS, "uninstall")
        uninstall_label = Gtk.Label(label="⚠️ Uninstall")
        self.notebook.append_page(uninstall_box, uninstall_label)

        # Create About tab
        help_box = self._create_help_tab()
        help_label = Gtk.Label(label="ℹ️ About")
        self.notebook.append_page(help_box, help_label)

        # Add top section to paned widget
        main_paned.pack1(top_box, True, True)

        # Bottom section - embedded terminal
        terminal_frame = Gtk.Frame()
        terminal_frame.set_shadow_type(Gtk.ShadowType.IN)
        
        # Terminal header with controls
        terminal_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        terminal_header_box.set_margin_top(6)
        terminal_header_box.set_margin_bottom(6)
        terminal_header_box.set_margin_start(6)
        terminal_header_box.set_margin_end(6)
        
        terminal_label = Gtk.Label(label="<b>Terminal Output</b>")
        terminal_label.set_use_markup(True)
        terminal_header_box.pack_start(terminal_label, False, False, 0)
        
        # Add clear button
        clear_button = Gtk.Button(label="Clear")
        clear_button.connect("clicked", self.on_terminal_clear)
        terminal_header_box.pack_end(clear_button, False, False, 0)
        
        # Terminal widget
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        terminal_box.pack_start(terminal_header_box, False, False, 0)
        
        # Create VTE terminal
        self.terminal = Vte.Terminal()
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_scroll_on_keystroke(True)
        self.terminal.set_scrollback_lines(10000)
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        
        # Set terminal colors (dark theme)
        fg_color = Gdk.RGBA()
        fg_color.parse("#EBEBEB")
        bg_color = Gdk.RGBA()
        bg_color.parse("#1E1E1E")
        self.terminal.set_color_foreground(fg_color)
        self.terminal.set_color_background(bg_color)
        
        # Enable right-click context menu
        self.terminal.connect("button-press-event", self.on_terminal_button_press)
        
        # Scrolled window for terminal
        terminal_scroll = Gtk.ScrolledWindow()
        terminal_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        terminal_scroll.add(self.terminal)
        terminal_box.pack_start(terminal_scroll, True, True, 0)
        
        terminal_frame.add(terminal_box)
        
        # Add terminal section to paned widget (initially small)
        main_paned.pack2(terminal_frame, False, True)
        main_paned.set_position(350)  # Initial split position - give more space to terminal

        # Track current tab
        self.current_tab = "install"
        self.notebook.connect("switch-page", self.on_tab_switched)

        # wire search -> both filters
        self.header_search.connect("search-changed", self.on_search_changed)

        # Initialize terminal with bash shell
        GLib.idle_add(self._init_terminal)

        # Check required packages on launch
        GLib.idle_add(self.check_required_packages)

    def _init_terminal(self):
        """Initialize the terminal with a bash shell"""
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.getcwd(),
            ["/bin/bash"],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            None
        )
        return False  # Remove idle handler

    def _create_script_tab(self, scripts, descriptions, tab_name):
        """Create a tab with script list and description panel"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        main_box.set_border_width(12)

        # Get the appropriate names array
        if tab_name == "install":
            names = SCRIPT_NAMES
        elif tab_name == "tools":
            names = TOOLS_NAMES
        elif tab_name == "exercises":
            names = EXERCISES_NAMES
        else:
            names = UNINSTALL_NAMES

        # store: display name, full path, description
        liststore = Gtk.ListStore(str, str, str)
        for i, script_path in enumerate(scripts):
            liststore.append([names[i], script_path, descriptions[i]])

        # filtered model driven by search entry
        filter_model = liststore.filter_new()
        filter_model.set_visible_func(self._filter_func, tab_name)

        # Store references for both tabs
        if tab_name == "install":
            self.install_liststore = liststore
            self.install_filter = filter_model
        elif tab_name == "tools":
            self.tools_liststore = liststore
            self.tools_filter = filter_model
        elif tab_name == "exercises":
            self.exercises_liststore = liststore
            self.exercises_filter = filter_model
        else:
            self.uninstall_liststore = liststore
            self.uninstall_filter = filter_model

        treeview = Gtk.TreeView(model=filter_model)
        treeview.set_name("treeview")
        renderer = Gtk.CellRendererText()
        
        # Set column header based on tab type
        if tab_name == "install":
            column_header = "Available Installs"
        elif tab_name == "tools":
            column_header = "Available Tools"
        elif tab_name == "exercises":
            column_header = "Bash Exercises"
        elif tab_name == "uninstall":
            column_header = "Uninstall Options"
        else:
            column_header = "Scripts"
        
        column = Gtk.TreeViewColumn(column_header, renderer, text=0)
        treeview.append_column(column)
        treeview.set_activate_on_single_click(False)
        treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        # double-click/enter to run
        treeview.connect("row-activated", self.on_row_activated)
        # selection changed handler
        treeview.get_selection().connect("changed", self.on_selection_changed)

        # Store treeview reference
        if tab_name == "install":
            self.install_treeview = treeview
        elif tab_name == "tools":
            self.tools_treeview = treeview
        elif tab_name == "exercises":
            self.exercises_treeview = treeview
        else:
            self.uninstall_treeview = treeview

        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(False)
        scroll.set_vexpand(True)
        scroll.set_min_content_width(260)
        scroll.set_name("scroll")
        scroll.add(treeview)
        main_box.pack_start(scroll, False, False, 0)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.pack_start(right_box, True, True, 0)

        # Description area
        description_label = Gtk.Label()
        description_label.set_line_wrap(True)
        description_label.set_name("desc_label")
        description_label.set_xalign(0)
        description_label.set_use_markup(True)
        description_label.set_selectable(True)
        description_label.connect("activate-link", self.on_link_clicked)
        description_label.set_text("Select a script to see description.")
        description_label.set_margin_top(6)
        description_label.set_margin_bottom(6)
        description_label.set_margin_start(6)
        description_label.set_margin_end(6)

        # Store label reference
        if tab_name == "install":
            self.install_description_label = description_label
        elif tab_name == "tools":
            self.tools_description_label = description_label
        elif tab_name == "exercises":
            self.exercises_description_label = description_label
        else:
            self.uninstall_description_label = description_label

        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_vexpand(True)
        desc_scroll.set_hexpand(True)
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.add(description_label)
        right_box.pack_start(desc_scroll, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_homogeneous(True)  # Make buttons equal width
        right_box.pack_end(button_box, False, False, 0)

        view_button = Gtk.Button(label="View Script")
        view_button.set_sensitive(False)
        view_button.connect("clicked", self.on_view_clicked)
        button_box.pack_start(view_button, True, True, 0)

        cd_button = Gtk.Button(label="Go to Directory")
        cd_button.set_sensitive(False)
        cd_button.connect("clicked", self.on_cd_clicked)
        button_box.pack_start(cd_button, True, True, 0)

        run_button = Gtk.Button(label="Run Script in Terminal")
        run_button.set_sensitive(False)
        run_button.get_style_context().add_class("suggested-action")
        run_button.connect("clicked", self.on_run_clicked)
        button_box.pack_start(run_button, True, True, 0)

        # Store button references
        if tab_name == "install":
            self.install_view_button = view_button
            self.install_cd_button = cd_button
            self.install_run_button = run_button
        elif tab_name == "tools":
            self.tools_view_button = view_button
            self.tools_cd_button = cd_button
            self.tools_run_button = run_button
        elif tab_name == "exercises":
            self.exercises_view_button = view_button
            self.exercises_cd_button = cd_button
            self.exercises_run_button = run_button
        else:
            self.uninstall_view_button = view_button
            self.uninstall_cd_button = cd_button
            self.uninstall_run_button = run_button

        return main_box

    def on_tab_switched(self, notebook, page, page_num):
        """Handle tab switching"""
        if page_num == 0:
            self.current_tab = "install"
        elif page_num == 1:
            self.current_tab = "tools"
        elif page_num == 2:
            self.current_tab = "exercises"
        elif page_num == 3:
            self.current_tab = "uninstall"
        else:
            return  # About tab, no filter needed
        # Reapply search filter
        self.on_search_changed(self.header_search)

    def get_current_widgets(self):
        """Get widgets for current tab"""
        if self.current_tab == "install":
            return {
                'treeview': self.install_treeview,
                'description_label': self.install_description_label,
                'run_button': self.install_run_button,
                'view_button': self.install_view_button,
                'cd_button': self.install_cd_button,
                'filter': self.install_filter,
                'scripts': SCRIPTS,
                'descriptions': DESCRIPTIONS
            }
        elif self.current_tab == "tools":
            return {
                'treeview': self.tools_treeview,
                'description_label': self.tools_description_label,
                'run_button': self.tools_run_button,
                'view_button': self.tools_view_button,
                'cd_button': self.tools_cd_button,
                'filter': self.tools_filter,
                'scripts': TOOLS_SCRIPTS,
                'descriptions': TOOLS_DESCRIPTIONS
            }
        elif self.current_tab == "exercises":
            return {
                'treeview': self.exercises_treeview,
                'description_label': self.exercises_description_label,
                'run_button': self.exercises_run_button,
                'view_button': self.exercises_view_button,
                'cd_button': self.exercises_cd_button,
                'filter': self.exercises_filter,
                'scripts': EXERCISES_SCRIPTS,
                'descriptions': EXERCISES_DESCRIPTIONS
            }
        else:
            return {
                'treeview': self.uninstall_treeview,
                'description_label': self.uninstall_description_label,
                'run_button': self.uninstall_run_button,
                'view_button': self.uninstall_view_button,
                'cd_button': self.uninstall_cd_button,
                'filter': self.uninstall_filter,
                'scripts': UNINSTALL_SCRIPTS,
                'descriptions': UNINSTALL_DESCRIPTIONS
            }

    def _create_help_tab(self):
        """Create About tab"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_border_width(20)
        
        # Scrollable container for content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        
        # Create a viewport to hold the label (required for proper scrolling)
        viewport = Gtk.Viewport()
        
        # Content label with markup
        content = Gtk.Label()
        content.set_use_markup(True)
        content.set_line_wrap(True)
        content.set_xalign(0)
        content.set_yalign(0)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        about_text = (
            "<big><b>Setup Tool</b></big>\n"
            "<i>Ubuntu Linux Setup &amp; Management Utility</i>\n\n"
            "<b>Version:</b> 2.0\n"
            "<b>Repository:</b> lv_linux_learn\n\n"
            "<span size='large'><b>About</b></span>\n\n"
            "This tool provides a graphical interface for installing and managing "
            "software packages on Ubuntu Linux. It simplifies the setup process for "
            "common development tools, applications, and utilities.\n\n"
            "<b>Features:</b>\n"
            "  • Install popular applications and development tools\n"
            "  • Safely uninstall packages with complete cleanup\n"
            "  • VPN setup and management (ZeroTier, NordVPN)\n"
            "  • Docker and container tools\n"
            "  • Git and GitHub CLI integration\n"
            "  • Desktop application installers\n\n"
            "<span size='large'><b>Credits</b></span>\n\n"
            "<b>Developer:</b> Adam Matson\n"
            "<b>GitHub:</b> <a href='https://github.com/amatson97'>@amatson97</a>\n"
            "<b>Repository:</b> <a href='https://github.com/amatson97/lv_linux_learn'>lv_linux_learn</a>\n\n"
            "<b>Target Platform:</b> Ubuntu Desktop 24.04.3 LTS\n\n"
            "<span size='large'><b>License</b></span>\n\n"
            "This project is open source and available under the MIT License.\n\n"
            "<span size='large'><b>Support</b></span>\n\n"
            "For issues, feature requests, or contributions, please visit the GitHub repository.\n\n"
            "<small><i>© 2025 Adam Matson. All rights reserved.</i></small>"
        )
        
        content.set_markup(about_text)
        content.connect("activate-link", self.on_link_clicked)
        
        # Add label to viewport, then viewport to scroll
        viewport.add(content)
        scroll.add(viewport)
        box.pack_start(scroll, True, True, 0)
        
        return box

    def check_required_packages(self):
        """Check for required packages and prompt to install if missing"""
        missing = []
        for pkg in REQUIRED_PACKAGES:
            if not self.command_exists(pkg):
                missing.append(pkg)
        
        if missing:
            self.show_install_prompt(missing)
        else:
            # Check optional packages and inform user
            missing_optional = []
            for pkg in OPTIONAL_PACKAGES:
                if not self.command_exists(pkg):
                    missing_optional.append(pkg)
            
            if missing_optional:
                self.show_optional_packages_info(missing_optional)
        
        return False  # remove idle handler after run once

    def _filter_func(self, model, iter, tab_name):
        if not hasattr(self, 'filter_text'):
            self.filter_text = ""
        if not self.filter_text:
            return True
        name = model[iter][0].lower()
        path = model[iter][1].lower()
        return self.filter_text in name or self.filter_text in path

    def on_search_changed(self, entry):
        self.filter_text = entry.get_text().strip().lower()
        self.install_filter.refilter()
        self.tools_filter.refilter()
        self.exercises_filter.refilter()
        self.uninstall_filter.refilter()

    def command_exists(self, cmd):
        from shutil import which
        return which(cmd) is not None

    def show_install_prompt(self, missing_pkgs):
        """Prompt user to install missing required packages"""
        pkg_list = ", ".join(missing_pkgs)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Missing Required Packages",
        )
        dialog.format_secondary_text(
            f"The following packages are required for this application:\n\n{pkg_list}\n\n"
            "Would you like to install them now?\n"
            "(This will run: sudo apt-get install)"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self.install_packages(missing_pkgs)
        else:
            # User declined install, warn and exit
            warn = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Cannot continue without required packages. Exiting.",
            )
            warn.run()
            warn.destroy()
            Gtk.main_quit()
            sys.exit(1)
    
    def show_optional_packages_info(self, missing_optional):
        """Inform user about missing optional packages"""
        pkg_list = ", ".join(missing_optional)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Optional Packages Available",
        )
        dialog.format_secondary_text(
            f"The following optional packages can enhance your experience:\n\n{pkg_list}\n\n"
            "These provide syntax highlighting when viewing scripts.\n"
            "Install with: sudo apt-get install bat (or pygmentize/highlight)"
        )
        dialog.run()
        dialog.destroy()

    def install_packages(self, pkgs):
        # Use sudo apt-get install to install missing packages
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y"] + pkgs, check=True)
        except subprocess.CalledProcessError:
            err = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Failed to install required packages. Please install them manually.",
            )
            err.run()
            err.destroy()
            Gtk.main_quit()
            sys.exit(1)

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        widgets = self.get_current_widgets()
        
        if treeiter is not None:
            # model is filtered -> get data from model columns
            basename = model[treeiter][0]
            fullpath = model[treeiter][1]
            desc_markup_raw = model[treeiter][2]
            
            # Build a compact header: bold filename + monospaced path, then description.
            safe_name = GLib.markup_escape_text(basename)
            safe_path = GLib.markup_escape_text(fullpath)
            desc_markup = (
                f"<big><b>{safe_name}</b></big>\n"
                f"<tt>{safe_path}</tt>\n\n"
                f"{desc_markup_raw}"
            )
            widgets['description_label'].set_markup(desc_markup)
            widgets['run_button'].set_sensitive(True)
            widgets['view_button'].set_sensitive(True)
            widgets['cd_button'].set_sensitive(True)
        else:
            widgets['description_label'].set_text("Select a script to see description.")
            widgets['run_button'].set_sensitive(False)
            widgets['view_button'].set_sensitive(False)
            widgets['cd_button'].set_sensitive(False)

    def on_run_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        # model is filtered -> get full path from model column 1
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Convert to absolute path to work regardless of terminal's current directory
        abs_path = os.path.abspath(script_path)
        
        # Send command to terminal
        command = f"bash '{abs_path}'\n"
        self.terminal.feed_child(command.encode())

    def on_cd_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Get the directory containing the script
        script_dir = os.path.dirname(os.path.abspath(script_path))
        safe_dir = shlex.quote(script_dir)
        
        # Change directory in terminal
        cd_cmd = f"cd {safe_dir} && pwd\n"
        self.terminal.feed_child(cd_cmd.encode())
    
    def on_view_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Convert to absolute path to work regardless of terminal's current directory
        abs_path = os.path.abspath(script_path)
        safe_path = shlex.quote(abs_path)
        
        # Clear screen first, then view file with a clean header
        viewer_cmd = (
            f"clear; "
            f"echo ''; "
            f"echo '{'=' * 80}'; "
            f"echo 'Viewing: {abs_path}'; "
            f"echo '{'=' * 80}'; "
            f"echo ''; "
            f"if command -v batcat >/dev/null 2>&1; then "
            f"batcat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v bat >/dev/null 2>&1; then "
            f"bat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v pygmentize >/dev/null 2>&1; then "
            f"pygmentize -g -f terminal256 {safe_path}; "
            f"elif command -v highlight >/dev/null 2>&1; then "
            f"highlight -O ansi {safe_path}; "
            f"else cat -n {safe_path}; fi 2>/dev/null\n"
        )
        
        self.terminal.feed_child(viewer_cmd.encode())
        
        # Scroll terminal to top after a brief delay
        GLib.timeout_add(100, self._scroll_terminal_to_top)
    
    def on_terminal_clear(self, button):
        """Clear the terminal"""
        self.terminal.feed_child(b"clear\n")
    
    def on_terminal_button_press(self, widget, event):
        """Handle right-click on terminal to show context menu"""
        if event.button == 3:  # Right-click
            menu = Gtk.Menu()
            
            # Copy menu item
            copy_item = Gtk.MenuItem(label="Copy")
            copy_item.connect("activate", self.on_terminal_copy)
            menu.append(copy_item)
            
            # Paste menu item
            paste_item = Gtk.MenuItem(label="Paste")
            paste_item.connect("activate", self.on_terminal_paste)
            menu.append(paste_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            # Select All menu item
            select_all_item = Gtk.MenuItem(label="Select All")
            select_all_item.connect("activate", self.on_terminal_select_all)
            menu.append(select_all_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            # Clear menu item
            clear_item = Gtk.MenuItem(label="Clear")
            clear_item.connect("activate", lambda w: self.terminal.feed_child(b"clear\n"))
            menu.append(clear_item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False
    
    def on_terminal_copy(self, menu_item):
        """Copy selected text from terminal to clipboard"""
        self.terminal.copy_clipboard_format(Vte.Format.TEXT)
    
    def on_terminal_paste(self, menu_item):
        """Paste text from clipboard to terminal"""
        self.terminal.paste_clipboard()
    
    def on_terminal_select_all(self, menu_item):
        """Select all text in terminal"""
        self.terminal.select_all()
    
    def _scroll_terminal_to_top(self):
        """Scroll the terminal viewport to the top"""
        adj = self.terminal.get_vadjustment()
        if adj:
            adj.set_value(adj.get_lower())
        return False  # Don't repeat the timeout

    def on_link_clicked(self, label, uri):
        webbrowser.open(uri)
        return True

    def on_row_activated(self, tree_view, path, column):
        # emulate run on double-click or Enter
        sel = tree_view.get_selection()
        sel.select_path(path)
        self.on_run_clicked(None)

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()


def on_activate(app):
    # set a default application icon for better GNOME integration (if available)
    assets_dir = Path(__file__).parent / "assets"
    icon_file = assets_dir / "menu_icon.png"
    if icon_file.exists():
        try:
            app.set_default_icon_from_file(str(icon_file))
        except Exception:
            pass

    win = ScriptMenuGTK(app)
    win.show_all()


def main():
    application_id = "com.lv.lv_linux_learn.menu"
    app = Gtk.Application(application_id=application_id)
    app.connect("activate", on_activate)
    # run() handles main loop and integrates with the session (startup notification, WM association)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())