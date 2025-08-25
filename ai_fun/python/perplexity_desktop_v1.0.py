#!/usr/bin/env python3
# Tested this works, outputs as text in the GUI.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import requests
import datetime
import json
import os

API_URL = 'https://api.perplexity.ai/chat/completions'

class PerplexityApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Perplexity AI Desktop Chat")
        self.set_default_size(780, 550)

        vbox = Gtk.VBox(spacing=8)
        self.add(vbox)

        # API key section
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        hbox_key = Gtk.HBox(spacing=5)
        vbox.pack_start(hbox_key, False, False, 0)
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("API Key (not stored on disk!)")
        self.key_entry.set_text(self.api_key)
        hbox_key.pack_start(Gtk.Label(label="API Key:"), False, False, 0)
        hbox_key.pack_start(self.key_entry, True, True, 0)

        # Prompt input
        self.prompt_buffer = Gtk.TextBuffer()
        prompt_view = Gtk.TextView(buffer=self.prompt_buffer)
        prompt_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        prompt_view.set_size_request(-1, 120)
        vbox.pack_start(Gtk.Label(label="Your prompt or code (multi-line allowed):"), False, False, 0)
        vbox.pack_start(prompt_view, False, False, 0)

        # Send and Save buttons
        send_btn = Gtk.Button(label="Send to Perplexity")
        send_btn.connect("clicked", self.on_send_clicked)
        self.save_btn = Gtk.Button(label="Save as Markdown (.md)")
        self.save_btn.set_sensitive(False)
        self.save_btn.connect("clicked", self.on_save_clicked)
        hbox_btns = Gtk.HBox(spacing=5)
        hbox_btns.pack_start(send_btn, False, False, 0)
        hbox_btns.pack_start(self.save_btn, False, False, 0)
        vbox.pack_start(hbox_btns, False, False, 0)

        # Response output
        self.response_buffer = Gtk.TextBuffer()
        self.response_view = Gtk.TextView(buffer=self.response_buffer)
        self.response_view.set_editable(False)
        self.response_view.set_wrap_mode(Gtk.WrapMode.WORD)
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_size_request(-1, 260)
        sw.add(self.response_view)
        vbox.pack_start(Gtk.Label(label="Response from Perplexity:"), False, False, 0)
        vbox.pack_start(sw, True, True, 0)

        self.citations = []
        self.prompt_text = ""
        self.response_text = ""

    def on_send_clicked(self, button):
        api_key = self.key_entry.get_text().strip()
        if not api_key:
            self.dialog_message("API Key missing! Enter your key to continue.", Gtk.MessageType.ERROR)
            return
        # Get prompt (all text in buffer)
        start, end = self.prompt_buffer.get_bounds()
        prompt = self.prompt_buffer.get_text(start, end, True)
        if not prompt.strip():
            self.dialog_message("Please enter a prompt.", Gtk.MessageType.WARNING)
            return

        # Compose JSON payload
        payload = {
            "model": "sonar-pro",
            "messages": [
                { "role": "user", "content": prompt }
            ],
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
                self.dialog_message(f"API Error: {res.status_code}\n{res.text}", Gtk.MessageType.ERROR)
                return
            data = res.json()
        except Exception as e:
            self.dialog_message(f"Network or request failed: {e}", Gtk.MessageType.ERROR)
            return

        # Parse result
        self.citations = data.get('citations', [])
        self.response_text = data['choices'][0]['message']['content'] if data.get('choices') else "(No content)"
        self.prompt_text = prompt

        # Display prettily
        display_txt = f"**Prompt:**\n{prompt}\n\n**Response:**\n{self.response_text}\n"
        if self.citations:
            display_txt += "\n**Citations:**\n"
            for c in self.citations:
                display_txt += f"- {c}\n"
        self.response_buffer.set_text(display_txt)
        self.save_btn.set_sensitive(True)

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
        # Write markdown
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Perplexity API Response\n\n")
            f.write(f"## Prompt\n")
            f.write("```")
            f.write(self.prompt_text)
            f.write("```\n\n")
            f.write(f"## Response\n")
            f.write("```")
            f.write(self.response_text)
            f.write("```\n\n")
            if self.citations:
                f.write("## Citations\n")
                for c in self.citations:
                    f.write(f"- {c}\n")
                f.write("\n")
        self.dialog_message(f"Response saved to:\n{filename}", Gtk.MessageType.INFO)

    def dialog_message(self, msg, mtype=Gtk.MessageType.INFO):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0, message_type=mtype,
            buttons=Gtk.ButtonsType.OK, text=msg
        )
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    app = PerplexityApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()