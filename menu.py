#!/usr/bin/env python3

import gi
import os
import subprocess
import webbrowser
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

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
    "  • <a href='https://www.zerotier.com/'>ZeroTier Official Site</a>\n"
    "  • <a href='https://www.wired.com/story/what-is-zerotier/'>Wired Intro</a>",

    "<b>Remove all VPN clients</b>\n"
    "• Uninstalls ZeroTier, NordVPN, LogMeIn Hamachi, and others to reset VPN state.\n"
    "• Helps resolve VPN conflicts and networking issues.\n"
    "Useful guides:\n"
    "  • <a href='https://nordvpn.com/help/how-to-uninstall-nordvpn/'>NordVPN Uninstall</a>\n"
    "  • <a href='https://vpn.net/knowledge-base/uninstall-logmein-hamachi/'>Hamachi Uninstall</a>",

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
    font-size: 16px;
    border-radius: 8px;
    padding: 12px;
}

headerbar {
    min-height: 36px;
    padding: 0 6px;
}

headerbar button.titlebutton {
    min-width: 24px;
    min-height: 24px;
    padding: 2px;
    margin: 0 2px;
    border-radius: 4px;
}

headerbar button.titlebutton:hover {
    background: #57606a;
}

button, GtkButton {
    border-radius: 6px;
    background: #444C56;
    color: #ebebeb;
    padding: 10px 20px;
    min-height: 36px;
    min-width: 100px;
    font-size: 16px;
}

button:hover, GtkButton:hover {
    background: #57606a;
}

#desc_label {
    margin-top: 8px;
    margin-bottom: 12px;
    font-style: italic;
    color: #ADB5BD;
}

.treeview {
    background: #1E1E1E;
    color: #ebebeb;
    border-radius: 6px;
    font-size: 16px;
}

.scroll {
    border-radius: 6px;
    background: #1E1E1E;
    box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.5);
}
"""

class ScriptMenuGTK(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Script Menu - External Terminal")
        self.set_default_size(840, 470)
        self.set_border_width(12)
        self.set_resizable(True)

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "VPN & Tools Script Menu"
        self.set_titlebar(hb)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(DARK_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.add(main_box)

        self.liststore = Gtk.ListStore(str)
        for script_path in SCRIPTS:
            self.liststore.append([os.path.basename(script_path)])

        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_name("treeview")
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Scripts", renderer, text=0)
        self.treeview.append_column(column)
        self.treeview.get_selection().connect("changed", self.on_selection_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(False)
        scroll.set_vexpand(True)
        scroll.set_min_content_width(260)
        scroll.set_name("scroll")
        scroll.add(self.treeview)
        main_box.pack_start(scroll, False, False, 0)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.pack_start(right_box, True, True, 0)

        self.description_label = Gtk.Label()
        self.description_label.set_line_wrap(True)
        self.description_label.set_name("desc_label")
        self.description_label.set_xalign(0)
        self.description_label.set_use_markup(True)
        self.description_label.connect("activate-link", self.on_link_clicked)
        self.description_label.set_text("Select a script to see description.")
        right_box.pack_start(self.description_label, False, False, 0)

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
            index = model.get_path(treeiter)[0]
            self.description_label.set_markup(DESCRIPTIONS[index])
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
        index = model.get_path(treeiter)[0]
        script_path = SCRIPTS[index]
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
        index = model.get_path(treeiter)[0]
        script_path = SCRIPTS[index]
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
                    f"cat '{script_path}'; echo ''; echo 'Press enter to close...'; read",
                ]
            )
        except FileNotFoundError:
            self.show_error_dialog("gnome-terminal not found. Please install or change terminal emulator.")

    def on_link_clicked(self, label, uri):
        webbrowser.open(uri)
        return True

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


def main():
    app = ScriptMenuGTK()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()