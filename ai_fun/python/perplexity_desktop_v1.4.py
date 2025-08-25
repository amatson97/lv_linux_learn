#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib
import requests
import datetime
import os
import threading
import stat
import hashlib

API_URL = 'https://api.perplexity.ai/chat/completions'
API_KEY_FILE = os.path.expanduser("~/.perplexity_api_key")

DARK_CSS = b"""
.textview {
  background: #232629;
  color: #ebebeb;
  font-family: 'Ubuntu Mono', 'monospace';
  font-size: 13px;
  padding: 10px;
}
"""

class PerplexityApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Perplexity AI Desktop Chat")
        self.set_default_size(780, 600)
        self.set_border_width(10)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(DARK_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.VBox(spacing=8)
        self.add(vbox)

        self.api_key = self.load_api_key() or ""
        # Optional: print hash on startup for verification
        if self.api_key:
            hash_val = self.get_api_key_hash()
            if hash_val:
                print(f"Loaded API Key SHA-256: {hash_val}")

        hbox_key = Gtk.HBox(spacing=5)
        vbox.pack_start(hbox_key, False, False, 0)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("API Key")
        self.key_entry.set_text(self.api_key)
        hbox_key.pack_start(Gtk.Label(label="API Key:"), False, False, 0)
        hbox_key.pack_start(self.key_entry, True, True, 0)

        # Save API Key checkbox
        self.save_key_checkbox = Gtk.CheckButton(label="Save API Key")
        self.save_key_checkbox.set_active(bool(self.api_key))
        vbox.pack_start(self.save_key_checkbox, False, False, 0)

        self.prompt_buffer = Gtk.TextBuffer()
        prompt_view = Gtk.TextView(buffer=self.prompt_buffer)
        prompt_view.set_wrap_mode(Gtk.WrapMode.WORD)
        prompt_view.set_name("textview")

        scrolled_prompt = Gtk.ScrolledWindow()
        scrolled_prompt.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_prompt.set_size_request(-1, 120)
        scrolled_prompt.add(prompt_view)
        vbox.pack_start(Gtk.Label(label="Enter your prompt or code (multi-line allowed):"), False, False, 0)
        vbox.pack_start(scrolled_prompt, False, False, 0)

        hbox_btns = Gtk.HBox(spacing=5)
        vbox.pack_start(hbox_btns, False, False, 0)

        self.send_btn = Gtk.Button(label="Send to Perplexity")
        self.send_btn.connect("clicked", self.on_send_clicked)
        hbox_btns.pack_start(self.send_btn, False, False, 0)

        self.save_btn = Gtk.Button(label="Save as Markdown (.md)")
        self.save_btn.set_sensitive(False)
        self.save_btn.connect("clicked", self.on_save_clicked)
        hbox_btns.pack_start(self.save_btn, False, False, 0)

        self.spinner = Gtk.Spinner()
        hbox_btns.pack_start(self.spinner, False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_size_request(-1, 300)

        self.response_view = Gtk.TextView()
        self.response_view.set_editable(False)
        self.response_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.response_view.set_name("textview")
        sw.add(self.response_view)
        vbox.pack_start(Gtk.Label(label="Response from Perplexity (rendered):"), False, False, 0)
        vbox.pack_start(sw, True, True, 0)

        self.citations = []
        self.prompt_text = ""
        self.response_text = ""

    def save_api_key(self, key):
        try:
            with open(API_KEY_FILE, 'w') as f:
                f.write(key)
            os.chmod(API_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)  # permission 600
        except Exception as e:
            self.dialog_message(f"Failed to save API Key: {e}", Gtk.MessageType.ERROR)

    def load_api_key(self):
        try:
            if os.path.isfile(API_KEY_FILE):
                with open(API_KEY_FILE, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    def delete_api_key(self):
        try:
            if os.path.isfile(API_KEY_FILE):
                os.remove(API_KEY_FILE)
        except Exception:
            pass

    def get_api_key_hash(self):
        try:
            with open(API_KEY_FILE, 'rb') as f:
                file_data = f.read()
            sha256_hash = hashlib.sha256(file_data).hexdigest()
            return sha256_hash
        except Exception:
            return None

    def on_send_clicked(self, button):
        api_key = self.key_entry.get_text().strip()
        if not api_key:
            self.dialog_message("API Key missing! Enter your key to continue.", Gtk.MessageType.ERROR)
            return

        if self.save_key_checkbox.get_active():
            self.save_api_key(api_key)
        else:
            self.delete_api_key()

        start, end = self.prompt_buffer.get_bounds()
        prompt = self.prompt_buffer.get_text(start, end, True)
        if not prompt.strip():
            self.dialog_message("Please enter a prompt.", Gtk.MessageType.WARNING)
            return

        self.send_btn.set_sensitive(False)
        self.spinner.start()
        self.save_btn.set_sensitive(False)

        thread = threading.Thread(target=self.api_call_thread, args=(api_key, prompt))
        thread.daemon = True
        thread.start()

    def api_call_thread(self, api_key, prompt):
        payload = {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if not res.ok:
                GLib.idle_add(self.dialog_message, f"API Error: {res.status_code}\n{res.text}", Gtk.MessageType.ERROR)
                GLib.idle_add(self.finish_request)
                return
            data = res.json()
        except Exception as e:
            GLib.idle_add(self.dialog_message, f"Network or request failed: {e}", Gtk.MessageType.ERROR)
            GLib.idle_add(self.finish_request)
            return

        self.citations = data.get("citations", [])
        self.response_text = data["choices"][0]["message"]["content"] if data.get("choices") else "(No content)"
        self.prompt_text = prompt

        GLib.idle_add(self.update_response_view)
        GLib.idle_add(self.finish_request)

    def finish_request(self):
        self.send_btn.set_sensitive(True)
        self.spinner.stop()
        self.save_btn.set_sensitive(True)

    def update_response_view(self):
        text = "# Perplexity API Response\n\n"
        text += "## Prompt\n" + self.prompt_text.strip() + "\n\n"
        text += "## Response\n" + self.response_text.strip() + "\n\n"
        if self.citations:
            text += "## Citations\n"
            for c in self.citations:
                text += f"- {c}\n"
            text += "\n"

        buffer = self.response_view.get_buffer()
        buffer.set_text(text)  # plain text display, no markup parsing

    def on_save_clicked(self, button):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dialog = Gtk.FileChooserDialog(
            "Save as Markdown", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        dialog.set_current_name(f"perplexity_response_{ts}.md")
        dialog.set_do_overwrite_confirmation(True)
        resp = dialog.run()
        filename = dialog.get_filename() if resp == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not filename:
            return

        md = (
            f"# Perplexity API Response\n\n"
            f"## Prompt\n{self.prompt_text.strip()}\n"
            f"## Response\n{self.response_text.strip()}\n"
        )
        if self.citations:
            md += "## Citations\n"
            for c in self.citations:
                md += f"- {c}\n"
            md += "\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md)
        self.dialog_message(f"Response saved to:\n{filename}", Gtk.MessageType.INFO)

    def dialog_message(self, msg, mtype=Gtk.MessageType.INFO):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=mtype,
            buttons=Gtk.ButtonsType.OK,
            text=msg,
        )
        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    app = PerplexityApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()