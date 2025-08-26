# Perplexity API Response

## Prompt
Why wont my python application custom icon show when I launch the application. It shows in the ubuntu application menu but not in the side bar when running. I also have the below code in my programe.

Which says it is loading the icon sucsefully:

    def __init__(self):
        Gtk.Window.__init__(self, title="Perplexity AI Desktop Chat")
        self.set_default_size(780, 600)
        self.set_border_width(10)

        # Properly resolve and check icon path
        icon_path = os.path.expanduser('~/lv_linux_learn/ai_fun/python/assets/perplexity_desktop.png')
        icon_path = os.path.abspath(icon_path)
        if os.path.isfile(icon_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                self.set_icon(pixbuf)
                print(f"Custom icon loaded from {icon_path}")
            except Exception as e:
                print(f"Failed to load icon: {e}")
        else:
            print(f"Icon file not found: {icon_path}")
## Response
Your Python application's custom icon shows in the Ubuntu application menu but not in the sidebar (dock) when running because **GNOME Shell (and Ubuntu's dock) determines the running application's icon by matching the running process to its corresponding .desktop file, not by the icon set in your code**[1][2][3][5]. The icon you set with `self.set_icon()` affects the window decoration and task switcher, but not the dock.

**Key reasons and solutions:**

- **.desktop File Matching:** The dock uses the .desktop file to associate a running app with its icon. If your app is launched in a way that doesn't match the .desktop file's `Exec` or `StartupWMClass`, the dock can't associate the running window with the correct icon, so it shows a generic icon or "python3"[1][2][3][5].
- **StartupWMClass:** Adding the correct `StartupWMClass` to your .desktop file helps GNOME Shell map your running window to the .desktop entry[2][4]. You can get the WM_CLASS of your app by running it and using `xprop WM_CLASS` (on Xorg) or GNOME's debugger (on Wayland)[4].
- **.desktop File Location:** The .desktop file must be in `~/.local/share/applications/` (for user apps) or `/usr/share/applications/` (for system-wide apps)[3].
- **Exec Line:** The `Exec` line in the .desktop file should match how you launch your app. If you launch with `python3 myapp.py`, the .desktop file's `Exec` should do the same[1][3].
- **Icon Field:** The `Icon` field should point to your icon (without the file extension if it's in an icon theme directory; with full path and extension if not)[5].

**What you should do:**

1. **Create or edit your .desktop file** (e.g., `perplexity.desktop`) in `~/.local/share/applications/` with content similar to:

    ```
    [Desktop Entry]
    Name=Perplexity AI Desktop Chat
    Exec=python3 /home/youruser/lv_linux_learn/ai_fun/python/your_app.py
    Icon=/home/youruser/lv_linux_learn/ai_fun/python/assets/perplexity_desktop.png
    Type=Application
    StartupWMClass=Perplexity AI Desktop Chat
    ```

2. **Set the correct `StartupWMClass`:**
   - Run your app.
   - In a terminal, run `xprop WM_CLASS` and click your app window (on Xorg), or use GNOME's debugger on Wayland[4].
   - Copy the WM_CLASS value (e.g., "Perplexity AI Desktop Chat") and set it as `StartupWMClass` in the .desktop file[2][4].

3. **Update the `Exec` line** to match exactly how you launch the app from the terminal[1][3].

4. **Reload GNOME Shell** (press Alt+F2, type `r`, and press Enter) or log out and back in.

**Summary Table:**

| Problem           | Cause                                               | Solution                                      |
|-------------------|-----------------------------------------------------|-----------------------------------------------|
| Icon missing in dock | .desktop file mismatch or missing StartupWMClass   | Set correct Exec and StartupWMClass           |
| Shows python3 in dock | App not matched to .desktop entry                | Ensure Exec matches launch command            |
| Icon shows in menu but not dock | Icon set in code, not in .desktop file      | Set Icon in .desktop file                     |

**References:**  
[1] Discourse GNOME: App icon/tooltip in dash comes from .desktop file  
[2] Transmission issue: StartupWMClass fixes icon in dash  
[3] wxPython: .desktop file in ~/.local/share/applications/ needed  
[4] ItsFOSS: How to get WM_CLASS and fix missing icons  
[5] GNOME Discourse: .desktop file icon and dock behavior

If you follow these steps, your custom icon should appear in the Ubuntu dock/sidebar when your app is running.
## Citations
- https://discourse.gnome.org/t/in-the-gnome-shell-dash-the-application-icon-is-blank-and-app-shows-up-as-python-instead-of-its-real-name/5243
- https://github.com/transmission/transmission/issues/5812
- https://discuss.wxpython.org/t/how-to-set-an-apps-icon-in-the-dock-on-linux-solved/36647
- https://itsfoss.com/ubuntu-app-icon-missing/
- https://discourse.gnome.org/t/svg-icon-in-desktop-file-no-longer-shows-in-dock-when-app-opens-gear-icon-instead/9647

