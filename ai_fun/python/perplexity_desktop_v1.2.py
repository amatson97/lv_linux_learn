#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import requests
import datetime
import os

API_URL = 'https://api.perplexity.ai/chat/completions'

DARK_CSS = b"""
.textview {
    background: #232629;
    color: #ebebeb;
    font-family: 'Ubuntu Mono', 'monospace';
    font-size: 13px;
    padding: 10px;
}
"""

def escape(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def markdown_to_pango(markdown):
    lines = markdown.splitlines()
    markup = []
    in_code = False
    for line in lines:
        strip_line = line.strip()
        if strip_line.startswith('```'):
            if not in_code:
                markup.append('<span foreground="orange"><tt>')
                in_code = True
            else:
                markup.append('</tt></span>')
                in_code = False
            continue
        if in_code:
            markup.append(escape(line))
        else:
            if strip_line.startswith('### '):
                markup.append(f'<span weight="bold" size="large">{escape(strip_line[4:])}</span>')
            elif strip_line.startswith('## '):
                markup.append(f'<span weight="bold" size="x-large">{escape(strip_line[3:])}</span>')
            elif strip_line.startswith('# '):
                markup.append(f'<span weight="bold" size="xx-large">{escape(strip_line[2:])}</span>')
            elif strip_line.startswith('- '):
                markup.append(f'-  {escape(strip_line[2:])}')
            elif '**' in strip_line:
                parts = line.split('**')
                boldified = ''
                for i, p in enumerate(parts):
                    if i % 2 == 1:
                        boldified += f'<b>{escape(p)}</b>'
                    else:
                        boldified += escape(p)
                markup.append(boldified)
            else:
                markup.append(escape(line))
    return '\n'.join(markup)

class PerplexityApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Perplexity AI Desktop Chat")
        self.set_default_size(780, 600)
        self.set_border_width(10)

        # Dark theme CSS
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(DARK_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.VBox(spacing=8)
        self.add(vbox)

        # API key input
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        hbox_key = Gtk.HBox(spacing=5)
        vbox.pack_start(hbox_key, False, False, 0)
        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("API Key")
        self.key_entry.set_text(self.api_key)
        hbox_key.pack_start(Gtk.Label(label="API Key:"), False, False, 0)
        hbox_key.pack_start(self.key_entry, True, True, 0)

        # Prompt input text box
        self.prompt_buffer = Gtk.TextBuffer()
        prompt_view = Gtk.TextView(buffer=self.prompt_buffer)
        prompt_view.set_wrap_mode(Gtk.WrapMode.WORD)
        prompt_view.set_size_request(-1, 120)
        prompt_view.set_name("textview")
        vbox.pack_start(Gtk.Label(label="Enter your prompt or code (multi-line allowed):"), False, False, 0)
        vbox.pack_start(prompt_view, False, False, 0)

        # Buttons: Send and Save
        send_btn = Gtk.Button(label="Send to Perplexity")
        send_btn.connect("clicked", self.on_send_clicked)
        self.save_btn = Gtk.Button(label="Save as Markdown (.md)")
        self.save_btn.set_sensitive(False)
        self.save_btn.connect("clicked", self.on_save_clicked)
        hbox_btns = Gtk.HBox(spacing=5)
        hbox_btns.pack_start(send_btn, False, False, 0)
        hbox_btns.pack_start(self.save_btn, False, False, 0)
        vbox.pack_start(hbox_btns, False, False, 0)

        # Response output text view, will show rich Pango markup
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

    def on_send_clicked(self, button):
        api_key = self.key_entry.get_text().strip()
        if not api_key:
            self.dialog_message("API Key missing! Enter your key to continue.", Gtk.MessageType.ERROR)
            return

        start, end = self.prompt_buffer.get_bounds()
        prompt = self.prompt_buffer.get_text(start, end, True)
        if not prompt.strip():
            self.dialog_message("Please enter a prompt.", Gtk.MessageType.WARNING)
            return

        payload = {
            "model": "sonar-pro",
            "messages": [ { "role": "user", "content": prompt } ],
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

        self.citations = data.get("citations", [])
        #self.response_text = data["choices"]["message"]["content"] if data.get("choices") else "(No content)"
        self.response_text = data["choices"][0]["message"]["content"] if data.get("choices") else "(No content)"
        self.prompt_text = prompt

        # Build the Markdown string for rendering & saving
        md = f"# Perplexity API Response\n\n"
        md += f"## Prompt\n```bash\n{prompt.strip()}\n```"
        md += f"## Response\n```\n{self.response_text.strip()}\n```"
        if self.citations:
            md += "## Citations\n"
            for c in self.citations:
                md += f"- {c}\n"
            md += "\n"

        # Convert markdown to pango markup and display
        markup_txt = markdown_to_pango(md)
        buffer = self.response_view.get_buffer()
        buffer.set_text("")  # clear previous content
        buffer.insert_markup(buffer.get_start_iter(), markup_txt, -1)

        self.save_btn.set_sensitive(True)

    def on_save_clicked(self, button):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dialog = Gtk.FileChooserDialog(
            "Save as Markdown", self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        dialog.set_current_name(f"perplexity_response_{ts}.md")
        dialog.set_do_overwrite_confirmation(True)
        resp = dialog.run()
        filename = dialog.get_filename() if resp == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not filename:
            return

        # Save plain markdown text (no markup)
        md = (
            f"# Perplexity API Response\n\n"
            f"## Prompt\n```\n{self.prompt_text.strip()}\n```\n"
            f"## Response\n```\n{self.response_text.strip()}\n```"
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