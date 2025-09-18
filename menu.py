import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

# Script filenames and descriptions arrays
SCRIPTS = [
    "scripts/new_vpn.sh",
    "scripts/remove_all_vpn.sh",
    "scripts/chrome_install.sh",
    "scripts/docker_install.sh",
    "scripts/git_setup.sh",
    "scripts/install_flatpak.sh",
    "scripts/sublime_install.sh",
    "scripts/git_setup.sh",
    "scripts/git_pull.sh",
    "scripts/git_push_changes.sh",
    "scripts/install_wine.sh",
    "scripts/nextcloud_client.sh",
]

DESCRIPTIONS = [
    "Installs ZeroTier VPN, joins Linux Learn Network, and removes conflicting VPNs.",
    "Removes all installed VPN clients including Zerotier, NordVPN, and LogMeIn Hamachi.",
    "Installs Google Chrome web browser for fast, secure internet browsing.",
    "Installs Docker including engine, CLI, containerd, and plugins for container management.",
    "Sets up Git and GitHub CLI with configuration and authentication for source control.",
    "Installs Flatpak and Flathub repository for easy access to universal Linux apps.",
    "Installs Sublime Text and Sublime Merge editors for code editing and version control.",
    "Guides you through setting up git in terminal.",
    "Allows you to pull all changes down from the GitHub repository.",
    "Allows you to add, commit and push all your changes to GitHub repository.",
    "Installs Wine/Winetricks and Microsoft Visual C++ 4.2 MFC runtime library (mfc42.dll).",
    "Install Nextcloud Desktop client, via flatpak.",
]

class ScriptMenuApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Script Menu - External Terminal")
        self.geometry("700x400")

        # Apply system theme
        style = ttk.Style(self)
        style.theme_use(style.theme_use())  # Use current native/system theme

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Available Scripts:").pack(anchor="w")

        self.listbox = tk.Listbox(frame, height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Show script file names in listbox
        for script_path in SCRIPTS:
            self.listbox.insert(tk.END, os.path.basename(script_path))

        # Label to display description
        self.desc_label = ttk.Label(frame, text="Select a script to see description.",
                                    wraplength=600, justify="left")
        self.desc_label.pack(pady=10)

        self.run_button = ttk.Button(frame, text="Run Script in Terminal", command=self.run_script)
        self.run_button.pack()
        self.run_button.state(["disabled"])

        exit_btn = ttk.Button(self, text="Exit", command=self.destroy)
        exit_btn.pack(pady=5)

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.desc_label.config(text=DESCRIPTIONS[index])
            self.run_button.state(["!disabled"])
        else:
            self.desc_label.config(text="Select a script to see description.")
            self.run_button.state(["disabled"])

    def run_script(self):
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        script_path = SCRIPTS[index]

        if not os.path.isfile(script_path):
            messagebox.showerror("Error", f"Script not found:\n{script_path}")
            return

        try:
            subprocess.Popen([
                "gnome-terminal",
                "--",
                "bash", "-c",
                f"bash '{script_path}'; echo 'Press enter to close...'; read"
            ])
        except FileNotFoundError:
            messagebox.showerror("Error", "gnome-terminal not found. Please install it or modify the script to use your terminal.")

if __name__ == "__main__":
    app = ScriptMenuApp()
    app.mainloop()