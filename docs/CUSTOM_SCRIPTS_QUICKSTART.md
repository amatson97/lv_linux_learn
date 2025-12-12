# Custom Scripts Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Open the Menu
```bash
cd ~/lv_linux_learn
./menu.py
```

### Step 2: Click the '+' Button
- Look for the '+' button next to any tab name:
  - 📦 Install **[+]**
  - 🔧 Tools **[+]**
  - 📚 Exercises **[+]**
  - ⚠️ Uninstall **[+]**

### Step 3: Fill in Your Script Details
```
Script Name:        My Awesome Script
Script Path:        /path/to/script.sh   [Browse...]
Description:        <b>What it does</b>
                    • Feature 1
                    • Feature 2
Requires sudo:      ☐ (check if needed)
                    
                    [Cancel]  [OK]
```

## 📝 Your Script Will Appear Like This:
```
Scripts List:
├── Chrome Install         (built-in)
├── Docker Install         (built-in)
└── 📝 My Awesome Script  (your custom script!)
```

## ✏️ Editing Scripts
1. **Right-click** on your script (the one with 📝)
2. Select **"✏️ Edit Script"**
3. Make changes
4. Click **OK**

## 🗑️ Deleting Scripts
1. **Right-click** on your script
2. Select **"🗑️ Delete Script"**
3. Confirm deletion
4. Done! (Your actual script file is NOT deleted)

## 🎯 Example: Add the Test Script

Try adding the included test script:

```
Script Name:        Test Custom Script
Script Path:        /home/adam/lv_linux_learn/test_custom_script.sh
Description:        <b>Test Custom Script</b>
                    Script: <tt>test_custom_script.sh</tt>
                    
                    • Demonstrates custom script feature
                    • Shows green_echo formatting
                    • Interactive example
Requires sudo:      ☐ (unchecked)
```

Then run it by:
1. Selecting it in the list
2. Clicking **"Run Script in Terminal"**
3. Watch it execute in the embedded terminal!

## 💡 Tips

### Make Your Script Executable
```bash
chmod +x /path/to/your/script.sh
```

### Use Green Echo for Nice Output
```bash
#!/bin/bash
source ~/lv_linux_learn/includes/main.sh

green_echo "[*] Starting my script..."
# Your code here
green_echo "[✓] Done!"
```

### Script Template
Save this as a template for new scripts:

```bash
#!/bin/bash

# Source shared functions
if [ -f "$HOME/lv_linux_learn/includes/main.sh" ]; then
    source "$HOME/lv_linux_learn/includes/main.sh"
fi

green_echo "╔════════════════════════════════════════╗"
green_echo "║   My Script Name                       ║"
green_echo "╚════════════════════════════════════════╝"

green_echo "[*] Step 1: Doing something..."
# Your code

green_echo "[*] Step 2: Doing more..."
# More code

green_echo "[✓] All done!"
read -p "Press Enter to continue..."
```

## 📍 Where Scripts Are Stored

Your custom script configurations are saved in:
```
~/.lv_linux_learn/custom_scripts.json
```

You can optionally store your actual scripts in:
```
~/.lv_linux_learn/scripts/
```

## ❓ Troubleshooting

### Script Doesn't Appear
- Make sure the file exists: `ls -lh /path/to/script.sh`
- Make sure it's executable: `chmod +x /path/to/script.sh`

### Can't Run Script
- Check the shebang line (first line): `#!/bin/bash`
- Try running it manually: `bash /path/to/script.sh`

### Right-Click Menu Not Working
- Only custom scripts (with 📝) have right-click menus
- Built-in scripts cannot be edited or deleted

## 🎓 Learn More

Full documentation: [CUSTOM_SCRIPTS.md](CUSTOM_SCRIPTS.md)

## 🌟 Examples of What You Can Add

- Your own installer scripts
- Backup automation tools
- File conversion utilities
- System maintenance scripts
- Custom deployment tools
- Testing and debugging helpers
- Anything you want!

**Happy scripting! 🚀**
