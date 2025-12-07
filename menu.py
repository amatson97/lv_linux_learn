#!/usr/bin/env python3

import gi
import os
import subprocess
import webbrowser
import sys
import shlex
from pathlib import Path

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
try:
    # optional nicer icons / pixbuf usage if available
    from gi.repository import GdkPixbuf
except Exception:
    GdkPixbuf = None

REQUIRED_PACKAGES = ["gnome-terminal", "bash", "cat"]

SCRIPTS = [
    "scripts/new_vpn.sh",
    "scripts/remove_all_vpn.sh",
    "scripts/chrome_install.sh",
    "scripts/docker_install.sh",
    "scripts/git_setup.sh",
    "scripts/install_flatpak.sh",
    "scripts/sublime_install.sh",
    "scripts/git_pull.sh",
    "scripts/git_push_changes.sh",
    "scripts/install_wine.sh",
    "scripts/nextcloud_client.sh",
]

DESCRIPTIONS = [
    "<b>Install ZeroTier VPN</b>\n"
    "• Joins the Linux Learn Network using ZeroTier, a flexible virtual network.\n"
    "• Removes conflicting VPN clients automatically.\n"
    "• Provides secure peer-to-peer virtual networking.\n"
    "More info:\n"
    "  • <a href='https://www.zerotier.com/'>ZeroTier Official Site</a>\n",

    "<b>Remove all VPN clients</b>\n"
    "• Uninstalls ZeroTier, NordVPN, LogMeIn Hamachi, and others to reset VPN state.\n"
    "• Helps resolve VPN conflicts and networking issues.\n",

    "<b>Install Google Chrome</b>\n"
    "• Adds official Google repository and keys to install stable Chrome.\n"
    "• Ensures latest browser improvements and security.\n"
    "Visit:\n"
    "  • <a href='https://www.google.com/chrome/'>Google Chrome Official</a>",

    "<b>Install Docker</b>\n"
    "• Installs Docker Engine, CLI, containerd, and plugins on Ubuntu.\n"
    "• Supports container management and orchestration.\n"
    "Docs:\n"
    "  • <a href='https://docs.docker.com/engine/install/ubuntu/'>Official Docker Install Guide</a>",

    "<b>Setup Git &amp; GitHub CLI</b>\n"
    "• Configures Git with user details.\n"
    "• Authenticates GitHub CLI for repository management.\n"
    "Learn more:\n"
    "  • <a href='https://cli.github.com/manual/'>GitHub CLI Manual</a>\n"
    "  • <a href='https://git-scm.com/doc'>Git Official Docs</a>",

    "<b>Install Flatpak &amp; Flathub</b>\n"
    "• Sets up Flatpak package manager.\n"
    "• Adds Flathub repository for universal Linux apps.\n"
    "Find out:\n"
    "  • <a href='https://flatpak.org/'>Flatpak Official Site</a>",

    "<b>Install Sublime Text &amp; Merge</b>\n"
    "• Installs Sublime Text editor and Sublime Merge Git client.\n"
    "• Features GPU rendering, context-aware autocomplete, refreshed UI.\n"
    "Explore:\n"
    "  • <a href='https://www.sublimetext.com/'>Sublime Text</a>\n"
    "  • <a href='https://www.sublimemerge.com/'>Sublime Merge</a>",

    "<b>Git Pull Changes</b>\n"
    "• Pulls latest changes from remote repositories.\n"
    "Details:\n"
    "  • <a href='https://git-scm.com/docs/git-pull'>Git Pull Documentation</a>",

    "<b>Git Push Changes</b>\n"
    "• Stages, commits, and pushes local changes to remote repo.\n"
    "Learn:\n"
    "  • <a href='https://git-scm.com/docs/git-push'>Git Push Documentation</a>",

    "<b>Install Wine &amp; Winetricks</b>\n"
    "• Installs Wine compatibility layer and Winetricks scripts.\n"
    "• Includes Microsoft Visual C++ 4.2 runtime setup.\n"
    "More info:\n"
    "  • <a href='https://wiki.winehq.org/Winetricks'>Winetricks Wiki</a>\n"
    "  • <a href='https://www.winehq.org/'>WineHQ</a>",

    "<b>Install Nextcloud Desktop Client</b>\n"
    "• Installs Nextcloud sync client via Flatpak.\n"
    "• Supports personal and enterprise Nextcloud servers.\n"
    "More reading:\n"
    "  • <a href='https://nextcloud.com/install/#install-clients'>Nextcloud Install Clients</a>\n"
    "  • <a href='https://docs.nextcloud.com/'>Nextcloud Documentation</a>",
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
        Gtk.ApplicationWindow.__init__(self, application=app, title="Main Menu")
        self.set_default_size(900, 520)
        self.set_border_width(12)
        self.set_resizable(True)

        # HeaderBar + integrated search (keeps GNOME decoration/behavior consistent)
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Main Menu"
        self.set_titlebar(hb)
        # add a small search entry to the headerbar for quick filtering
        self.header_search = Gtk.SearchEntry()
        self.header_search.set_placeholder_text("Search scripts...")
        self.header_search.set_size_request(240, -1)
        hb.pack_end(self.header_search)

        # Do not register a CSS provider — inherit system theme for native look & feel.
        # Removing custom styling avoids altering headerbar/titlebutton sizing and other
        # desktop-managed decorations that make the window look "native".

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.add(main_box)

        # store: display name, full path
        self.liststore = Gtk.ListStore(str, str)
        for script_path in SCRIPTS:
            self.liststore.append([os.path.basename(script_path), script_path])

        # filtered model driven by search entry
        self.filter_text = ""
        self.filter = self.liststore.filter_new()
        self.filter.set_visible_func(self._filter_func)

        self.treeview = Gtk.TreeView(model=self.filter)
        self.treeview.set_name("treeview")
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Scripts", renderer, text=0)
        self.treeview.append_column(column)
        self.treeview.set_activate_on_single_click(False)
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        # double-click/enter to run
        self.treeview.connect("row-activated", self.on_row_activated)
        # selection changed handler
        self.treeview.get_selection().connect("changed", self.on_selection_changed)
        # wire search -> filter
        self.header_search.connect("search-changed", self.on_search_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(False)
        scroll.set_vexpand(True)
        scroll.set_min_content_width(260)
        scroll.set_name("scroll")
        scroll.add(self.treeview)
        main_box.pack_start(scroll, False, False, 0)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.pack_start(right_box, True, True, 0)

        # Description area: use a scrollable, selectable label so long help text
        # uses the available right-side space and remains copyable.
        self.description_label = Gtk.Label()
        self.description_label.set_line_wrap(True)
        self.description_label.set_name("desc_label")
        self.description_label.set_xalign(0)
        self.description_label.set_use_markup(True)
        self.description_label.set_selectable(True)
        self.description_label.connect("activate-link", self.on_link_clicked)
        self.description_label.set_text("Select a script to see description.")
        # margins to give breathing room
        self.description_label.set_margin_top(6)
        self.description_label.set_margin_bottom(6)
        self.description_label.set_margin_start(6)
        self.description_label.set_margin_end(6)

        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_vexpand(True)
        desc_scroll.set_hexpand(True)
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.add(self.description_label)
        # pack the scrollable description to expand and use available space
        right_box.pack_start(desc_scroll, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        right_box.pack_end(button_box, False, False, 0)

        self.view_button = Gtk.Button(label="View Script")
        self.view_button.set_sensitive(False)
        self.view_button.connect("clicked", self.on_view_clicked)
        button_box.pack_start(self.view_button, False, False, 0)

        self.run_button = Gtk.Button(label="Run Script in Terminal")
        self.run_button.set_sensitive(False)
        self.run_button.get_style_context().add_class("suggested-action")
        self.run_button.connect("clicked", self.on_run_clicked)
        button_box.pack_start(self.run_button, False, False, 0)

        # keyboard accelerators (Ctrl+R run, Ctrl+V view)
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        key_r = Gdk.keyval_from_name("r")
        key_v = Gdk.keyval_from_name("v")
        self.run_button.add_accelerator("clicked", accel, key_r, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        self.view_button.add_accelerator("clicked", accel, key_v, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        # Check required packages on launch
        GLib.idle_add(self.check_required_packages)

    def check_required_packages(self):
        missing = []
        for pkg in REQUIRED_PACKAGES:
            if not self.command_exists(pkg):
                missing.append(pkg)
        if missing:
            self.show_install_prompt(missing)
        return False  # remove idle handler after run once

    def _filter_func(self, model, iter, data):
        if not self.filter_text:
            return True
        name = model[iter][0].lower()
        path = model[iter][1].lower()
        return self.filter_text in name or self.filter_text in path

    def on_search_changed(self, entry):
        self.filter_text = entry.get_text().strip().lower()
        self.filter.refilter()

    def command_exists(self, cmd):
        from shutil import which
        return which(cmd) is not None

    def show_install_prompt(self, missing_pkgs):
        pkg_list = ", ".join(missing_pkgs)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"The following required packages are missing:\n{pkg_list}\n\nInstall them now?",
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
        if treeiter is not None:
            # model is filtered -> get full path from model column 1
            fullpath = model[treeiter][1]
            try:
                idx = SCRIPTS.index(fullpath)
            except ValueError:
                idx = 0
            # Build a compact header: bold filename + monospaced path, then description.
            basename = os.path.basename(fullpath)
            safe_name = GLib.markup_escape_text(basename)
            safe_path = GLib.markup_escape_text(fullpath)
            desc_markup = (
                f"<big><b>{safe_name}</b></big>\n"
                f"<tt>{safe_path}</tt>\n\n"
                f"{DESCRIPTIONS[idx]}"
            )
            self.description_label.set_markup(desc_markup)
            self.run_button.set_sensitive(True)
            self.view_button.set_sensitive(True)
        else:
            self.description_label.set_text("Select a script to see description.")
            self.run_button.set_sensitive(False)
            self.view_button.set_sensitive(False)

    def on_run_clicked(self, button):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        # model is filtered -> get full path from model column 1
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        try:
            subprocess.Popen(
                [
                    "gnome-terminal",
                    "--",
                    "bash",
                    "-c",
                    f"bash '{script_path}'; echo 'Press enter to close...'; read",
                ]
            )
        except FileNotFoundError:
            self.show_error_dialog("gnome-terminal not found. Please install or change terminal emulator.")

    def on_view_clicked(self, button):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        # prefer colorizing viewers if available: bat -> pygmentize -> highlight -> cat
        safe_path = shlex.quote(script_path)
        viewer_cmd = (
            f"if command -v bat >/dev/null 2>&1; then "
            f"bat --paging=always --style=plain --color=always {safe_path}; "
            f"elif command -v pygmentize >/dev/null 2>&1; then "
            f"pygmentize -g -f terminal256 {safe_path}; "
            f"elif command -v highlight >/dev/null 2>&1; then "
            f"highlight -O ansi {safe_path}; "
            f"else cat {safe_path}; fi; echo ''; echo 'Press enter to close...'; read"
        )
        try:
            subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", viewer_cmd]
            )
        except FileNotFoundError:
            self.show_error_dialog("gnome-terminal not found. Please install or change terminal emulator.")

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