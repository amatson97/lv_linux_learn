#!/usr/bin/env python3
# sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 python3-requests
# Improvements: Gtk.Application integration, clipboard, Ctrl+Enter, env fallback, --cli mode.

import sys
import os
import threading
import datetime
import stat
import hashlib
import shlex
import json
import re
from pathlib import Path

# Guarded import for PyGObject
try:
    import gi
    if not hasattr(gi, "require_version"):
        raise ImportError("module 'gi' does not provide 'require_version' — PyGObject not installed")
    gi.require_version("Gtk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
except Exception as e:
    print("Error: PyGObject / GTK bindings are not available or misconfigured:", e)
    print("On Debian/Ubuntu install required packages and try again:")
    print("  sudo apt update && sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 python3-requests")
    sys.exit(1)

import requests

# API URL and KEY_FILE locations.
API_URL = "https://api.perplexity.ai/chat/completions"
API_KEY_FILE = os.path.expanduser("~/.perplexity_api_key")


class PerplexityWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.ApplicationWindow.__init__(self, application=app, title="Perplexity AI Desktop Chat")
        self.set_default_size(780, 600)
        self.set_border_width(10)

        # Optional icon
        icon_path = os.path.expanduser("~/lv_linux_learn/ai_fun/python/assets/perplexity_desktop.png")
        icon_path = os.path.abspath(icon_path)
        if os.path.isfile(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception:
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                    self.set_icon(pixbuf)
                except Exception:
                    pass

        # Layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(main_vbox)

        # API key row
        api_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(api_hbox, False, False, 0)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("API Key (or set PERPLEXITY_API_KEY)")
        self.key_entry.set_hexpand(True)
        api_hbox.pack_start(Gtk.Label(label="API Key:"), False, False, 0)
        api_hbox.pack_start(self.key_entry, True, True, 0)

        self.save_key_checkbox = Gtk.CheckButton(label="Save API Key")
        api_hbox.pack_start(self.save_key_checkbox, False, False, 0)
        self.save_key_checkbox.connect("toggled", self.on_save_key_toggled)

        self.delete_api_key_button = Gtk.Button(label="Delete API Key")
        self.delete_api_key_button.connect("clicked", self.on_delete_api_key_clicked)
        api_hbox.pack_start(self.delete_api_key_button, False, False, 0)

        # Load API key: saved file first, then ENV fallback
        saved = self.load_api_key()
        env_key = os.environ.get("PERPLEXITY_API_KEY")
        if saved:
            self.key_entry.set_text(saved)
            self.save_key_checkbox.set_active(True)
        elif env_key:
            self.key_entry.set_text(env_key)
            self.save_key_checkbox.set_active(False)

        # Prompt area
        prompt_label = Gtk.Label(label="Enter your prompt or code (multi-line allowed):")
        prompt_label.set_halign(Gtk.Align.START)
        main_vbox.pack_start(prompt_label, False, False, 0)

        self.prompt_buffer = Gtk.TextBuffer()
        prompt_view = Gtk.TextView(buffer=self.prompt_buffer)
        prompt_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scrolled_prompt = Gtk.ScrolledWindow()
        scrolled_prompt.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_prompt.set_size_request(-1, 140)
        scrolled_prompt.add(prompt_view)
        main_vbox.pack_start(scrolled_prompt, False, False, 0)

        # Buttons row (Send, Save, Copy, Clear) + spinner
        btn_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(btn_hbox, False, False, 0)

        self.send_btn = Gtk.Button(label="Send to Perplexity")
        self.send_btn.connect("clicked", self.on_send_clicked)
        btn_hbox.pack_start(self.send_btn, False, False, 0)

        self.save_btn = Gtk.Button(label="Save as Markdown (.md)")
        self.save_btn.set_sensitive(False)
        self.save_btn.connect("clicked", self.on_save_clicked)
        btn_hbox.pack_start(self.save_btn, False, False, 0)

        self.copy_btn = Gtk.Button(label="Copy Response")
        self.copy_btn.set_sensitive(False)
        self.copy_btn.connect("clicked", self.on_copy_clicked)
        btn_hbox.pack_start(self.copy_btn, False, False, 0)

        self.clear_btn = Gtk.Button(label="Clear")
        self.clear_btn.connect("clicked", self.on_clear_clicked)
        btn_hbox.pack_start(self.clear_btn, False, False, 0)

        # Response format selector + render toggle
        self.format_combo = Gtk.ComboBoxText()
        for opt in ("Plain", "Markdown", "JSON", "Shell"):
            self.format_combo.append_text(opt)
        self.format_combo.set_active(0)
        btn_hbox.pack_start(Gtk.Label(label="Format:"), False, False, 6)
        btn_hbox.pack_start(self.format_combo, False, False, 0)

        self.render_toggle = Gtk.ToggleButton(label="Render")
        self.render_toggle.set_active(True)
        btn_hbox.pack_start(self.render_toggle, False, False, 0)

        self.spinner = Gtk.Spinner()
        btn_hbox.pack_start(self.spinner, False, False, 0)

        # Response area
        resp_label = Gtk.Label(label="Response from Perplexity:")
        resp_label.set_halign(Gtk.Align.START)
        main_vbox.pack_start(resp_label, False, False, 0)

        self.response_view = Gtk.TextView()
        self.response_view.set_editable(False)
        self.response_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.response_view)
        sw.set_vexpand(True)
        main_vbox.pack_start(sw, True, True, 0)

        # Accelerator: Ctrl+Enter to send
        accel = Gtk.AccelGroup()
        self.add_accel_group(accel)
        key = Gdk.keyval_from_name("Return")
        self.send_btn.add_accelerator("clicked", accel, key, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

        # Key handler directly on TextView: Ctrl+Enter
        prompt_view.connect("key-press-event", self.on_prompt_keypress)

        # internal state
        self.citations = []
        self.prompt_text = ""
        self.response_text = ""
        self.last_response_format = "Plain"

        # Clipboard
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    # API key helpers
    def save_api_key(self, key):
        try:
            with open(API_KEY_FILE, "w") as f:
                f.write(key)
            os.chmod(API_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 600
        except Exception as e:
            self.dialog_message(f"Failed to save API Key: {e}", Gtk.MessageType.ERROR)

    def load_api_key(self):
        try:
            if os.path.isfile(API_KEY_FILE):
                with open(API_KEY_FILE, "r") as f:
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

    def on_delete_api_key_clicked(self, widget):
        self.delete_api_key()
        self.key_entry.set_text("")
        self.save_key_checkbox.set_active(False)

    def on_save_key_toggled(self, checkbox):
        api_key = self.key_entry.get_text().strip()
        if checkbox.get_active():
            if api_key:
                self.save_api_key(api_key)
            else:
                self.dialog_message("Cannot save empty API key.", Gtk.MessageType.WARNING)
                checkbox.set_active(False)
        else:
            self.delete_api_key()

    # Input handlers
    def on_prompt_keypress(self, widget, event):
        state = event.get_state()
        if (state & Gdk.ModifierType.CONTROL_MASK) and event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.on_send_clicked(None)
            return True
        return False

    def on_send_clicked(self, button):
        api_key = self.key_entry.get_text().strip() or os.environ.get("PERPLEXITY_API_KEY", "")
        if not api_key:
            self.dialog_message("API Key missing! Enter your key or set PERPLEXITY_API_KEY.", Gtk.MessageType.ERROR)
            return

        if self.save_key_checkbox.get_active():
            self.save_api_key(api_key)
        else:
            # prefer env or transient; do not keep file
            pass

        start, end = self.prompt_buffer.get_bounds()
        prompt = self.prompt_buffer.get_text(start, end, True)
        if not prompt.strip():
            self.dialog_message("Please enter a prompt.", Gtk.MessageType.WARNING)
            return

        # chosen format and rendering
        chosen_format = self.format_combo.get_active_text() or "Plain"
        self.last_response_format = chosen_format
        render_on = bool(self.render_toggle.get_active())

        # disable UI
        self.send_btn.set_sensitive(False)
        self.spinner.start()
        self.save_btn.set_sensitive(False)
        self.copy_btn.set_sensitive(False)

        # thread (include chosen format so we send the system instruction)
        thread = threading.Thread(target=self.api_call_thread, args=(api_key, prompt, chosen_format, render_on))
        thread.daemon = True
        thread.start()

    def api_call_thread(self, api_key, prompt, chosen_format="Plain", render_on=True):
        payload = {
            "model": "sonar-pro",
            # Prepend a small system instruction asking Perplexity to respond in chosen format.
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Respond ONLY in the requested format. "
                        f"Requested format: {chosen_format}. "
                        "If JSON is requested, return valid JSON only. "
                        "If Markdown is requested, use standard Markdown syntax. "
                        "If Shell is requested, return shell commands or scripts only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            GLib.idle_add(self.dialog_message, f"Network or request failed: {e}", Gtk.MessageType.ERROR)
            GLib.idle_add(self.finish_request)
            return

        if not res.ok:
            GLib.idle_add(self.dialog_message, f"API Error: {res.status_code}\n{res.text}", Gtk.MessageType.ERROR)
            GLib.idle_add(self.finish_request)
            return

        try:
            data = res.json()
        except ValueError:
            GLib.idle_add(self.dialog_message, "API returned invalid JSON.", Gtk.MessageType.ERROR)
            GLib.idle_add(self.finish_request)
            return

        # Defensive parsing of response content
        content = "(No content)"
        choices = data.get("choices")
        if isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            if isinstance(first, dict):
                content = (first.get("message", {}) or {}).get("content") or first.get("text") or str(first)
            else:
                content = str(first)
        else:
            content = data.get("text") or data.get("response") or content

        # Normalize citations
        raw_citations = data.get("citations") or []
        norm_citations = []
        if isinstance(raw_citations, list):
            for c in raw_citations:
                if isinstance(c, str):
                    norm_citations.append(c)
                elif isinstance(c, dict):
                    for k in ("url", "link", "href", "title", "text"):
                        if k in c and c[k]:
                            norm_citations.append(str(c[k]))
                            break
                    else:
                        norm_citations.append(str(c))
                else:
                    norm_citations.append(str(c))
        elif isinstance(raw_citations, str):
            norm_citations = [raw_citations]

        self.citations = norm_citations
        self.response_text = content
        self.prompt_text = prompt
        # remember format used by last response (for rendering). stored above already.
        GLib.idle_add(self.update_response_view)
        GLib.idle_add(self.finish_request)

    def finish_request(self):
        self.send_btn.set_sensitive(True)
        self.spinner.stop()
        self.save_btn.set_sensitive(True)
        self.copy_btn.set_sensitive(True)

    def update_response_view(self):
        # Build base text
        header = "# Perplexity API Response\n\n"
        header += "## Prompt\n" + self.prompt_text.strip() + "\n\n"
        header += "## Response\n"
        footer = "\n\n"
        if self.citations:
            footer += "## Citations\n"
            for c in self.citations:
                footer += f"- {c}\n"
            footer += "\n"

        raw = header + self.response_text.strip() + footer

        buf = self.response_view.get_buffer()
        # remove existing tags / content
        buf.set_text("")  # start fresh

        fmt = getattr(self, "last_response_format", "Plain")
        render_on = bool(self.render_toggle.get_active())

        if fmt == "JSON":
            # attempt to pretty-print JSON; otherwise show raw
            try:
                parsed = json.loads(self.response_text)
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                # show header + pretty JSON in monospace
                buf.insert(buf.get_end_iter(), header)
                start = buf.get_end_iter()
                buf.insert(start, pretty + footer)
                # create monospace tag and apply to JSON region
                tag = buf.create_tag("mono", family="monospace")
                # apply tag to the JSON region (calculate bounds)
                start_iter = buf.get_iter_at_offset(len(header))
                end_iter = buf.get_end_iter()
                buf.apply_tag(tag, start_iter, end_iter)
                return
            except Exception:
                # fallback to raw
                buf.set_text(raw)
                return

        if fmt == "Markdown" and render_on:
            # simple markdown rendering: bold headers, monospace for ```code```
            # insert header
            buf.insert(buf.get_end_iter(), header)
            body = self.response_text.strip() + footer
            # process code blocks first
            code_blocks = list(re.finditer(r"```(?:\w+\n)?(.*?)```", body, flags=re.S))
            last_pos = 0
            for m in code_blocks:
                pre = body[last_pos : m.start()]
                code = m.group(1)
                # insert pre (with basic header bolding)
                self._insert_with_basic_markup(buf, pre)
                # insert code block with monospace tag
                start_iter = buf.get_end_iter()
                buf.insert(start_iter, code + "\n")
                tag = buf.create_tag("mono", family="monospace", background="#f6f8fa")
                s = buf.get_iter_at_offset(buf.get_char_count() - len(code) - 1)
                e = buf.get_end_iter()
                buf.apply_tag(tag, s, e)
                last_pos = m.end()
            # remaining tail
            tail = body[last_pos:]
            self._insert_with_basic_markup(buf, tail)
            return

        # default: show raw text (or monospace if Shell)
        if fmt == "Shell":
            buf.set_text(raw)
            tag = buf.create_tag("mono", family="monospace")
            start_iter = buf.get_start_iter()
            end_iter = buf.get_end_iter()
            buf.apply_tag(tag, start_iter, end_iter)
            return

        # fallback plain / unrendered
        buf.set_text(raw)

    def _insert_with_basic_markup(self, buf, text):
        """
        Basic markup: bold headers (lines starting with #), plain otherwise.
        """
        for line in text.splitlines(True):
            if re.match(r"^#{1,6}\s+", line):
                # header
                # remove leading hashes for display, but keep in text
                display = line.lstrip("#").strip()
                start = buf.get_end_iter()
                buf.insert(start, display + "\n")
                tag = buf.create_tag("bold", weight=Pango.Weight.BOLD) if "Pango" in globals() else buf.create_tag("bold")
                s = buf.get_iter_at_offset(buf.get_char_count() - len(display) - 1)
                e = buf.get_end_iter()
                buf.apply_tag(tag, s, e)
            else:
                buf.insert(buf.get_end_iter(), line)
        return

    def on_save_clicked(self, button):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dialog = Gtk.FileChooserDialog(
            "Save as Markdown",
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
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
            f"## Prompt\n{self.prompt_text.strip()}\n\n"
            f"## Response\n{self.response_text.strip()}\n\n"
        )
        if self.citations:
            md += "## References\n"
            for c in self.citations:
                md += f"- {c}\n"
            md += "\n"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(md)
        except Exception as e:
            self.dialog_message(f"Failed to save file: {e}", Gtk.MessageType.ERROR)
            return

        self.dialog_message(f"Response saved to:\n{filename}", Gtk.MessageType.INFO)

    def on_copy_clicked(self, button):
        # Copy current response text to clipboard
        text = self.response_text.strip()
        if not text:
            self.dialog_message("No response to copy.", Gtk.MessageType.WARNING)
            return
        self.clipboard.set_text(text, -1)
        self.dialog_message("Response copied to clipboard.", Gtk.MessageType.INFO)

    def on_clear_clicked(self, button):
        # Clear prompt and response
        self.prompt_buffer.set_text("")
        self.response_view.get_buffer().set_text("")
        self.response_text = ""
        self.prompt_text = ""
        self.citations = []
        self.save_btn.set_sensitive(False)
        self.copy_btn.set_sensitive(False)

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


class PerplexityApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="com.lv.perplexity.desktop")

    def do_activate(self):
        win = PerplexityWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)


def run_cli_mode():
    # Simple headless runner for quick testing: reads prompt from stdin and writes response to stdout.
    api_key = os.environ.get("PERPLEXITY_API_KEY") or (open(API_KEY_FILE).read().strip() if os.path.exists(API_KEY_FILE) else "")
    if not api_key:
        print("API key required. Set PERPLEXITY_API_KEY or create ~/.perplexity_api_key")
        return 2
    prompt = sys.stdin.read().strip()
    if not prompt:
        print("No prompt provided on stdin.")
        return 1
    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        res = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        choices = data.get("choices")
        content = "(No content)"
        if isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            if isinstance(first, dict):
                content = (first.get("message", {}) or {}).get("content") or first.get("text") or str(first)
            else:
                content = str(first)
        else:
            content = data.get("text") or data.get("response") or content
        print(content)
        return 0
    except Exception as e:
        print("Request failed:", e)
        return 1


if __name__ == "__main__":
    # If --cli provided, run headless quick test path.
    if "--cli" in sys.argv:
        sys.exit(run_cli_mode())
    app = PerplexityApp()
    sys.exit(app.run(sys.argv))