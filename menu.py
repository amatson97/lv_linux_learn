#!/usr/bin/env python3

import gi
import os
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

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

# Fixed Pango markup descriptions with \n for line breaks (not <br/>)
DESCRIPTIONS = [
    "<b>Install ZeroTier VPN</b>\nJoins the Linux Learn Network and removes conflicting VPNs. Automates setup and simplifies VPN connectivity for container orchestration and remote access.",
    "<b>Remove all VPNs</b>\nRemoves installed VPN clients like Zerotier, NordVPN, LogMeIn Hamachi. Useful for cleanup and resetting VPN configurations.",
    "<b>Install Google Chrome</b>\nAdds Google's official repository and keys to install stable, up-to-date Chrome browser.",
    "<b>Install Docker</b>\nInstalls Docker engine, CLI, and plugins to set up a full container environment.",
    "<b>Setup Git &amp; GitHub CLI</b>\nConfigures Git with user credentials and authenticates GitHub CLI for source control.",
    "<b>Install Flatpak &amp; Flathub</b>\nAdds Flatpak support and Flathub repository for universal Linux apps.",
    "<b>Install Sublime Text &amp; Merge</b>\nInstalls popular code editors from official repositories.",
    "<b>Git Pull Changes</b>\nPulls remote changes from GitHub repositories, keeping local repos up-to-date.",
    "<b>Git Push Changes</b>\nAdds, commits, and pushes code changes with default or prompted messages.",
    "<b>Install Wine &amp; Winetricks</b>\nSets up Wine with Microsoft Visual C++ 4.2 runtime to run Windows apps on Linux.",
    "<b>Install Nextcloud Client</b>\nInstalls Nextcloud Desktop client via Flatpak for personal and enterprise cloud sync.",
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
        hb.props.title = "Script Menu - lv_linux_learn"
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
        self.description_label.set_text("Select a script to see description.")
        right_box.pack_start(self.description_label, False, False, 0)

        self.run_button = Gtk.Button(label="Run Script in Terminal")
        self.run_button.set_sensitive(False)
        self.run_button.get_style_context().add_class("suggested-action")
        self.run_button.connect("clicked", self.on_run_clicked)
        right_box.pack_end(self.run_button, False, False, 0)

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            index = model.get_path(treeiter)[0]
            self.description_label.set_markup(DESCRIPTIONS[index])
            self.run_button.set_sensitive(True)
        else:
            self.description_label.set_text("Select a script to see description.")
            self.run_button.set_sensitive(False)

    def on_run_clicked(self, button):
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        index = model.get_path(treeiter)[0]
        script_path = SCRIPTS[index]
        if not os.path.isfile(script_path):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Script not found:\n{script_path}",
            )
            dialog.run()
            dialog.destroy()
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
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="gnome-terminal not found. Please install or change terminal emulator.",
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