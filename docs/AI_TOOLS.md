# AI Integration Tools

Complete guide for Perplexity AI CLI and desktop applications.

## Table of Contents
1. [Enhanced Perplexity CLI (v1.1)](#enhanced-perplexity-cli-v11)
2. [Legacy Perplexity Script](#legacy-perplexity-script)
3. [Python Desktop Applications](#python-desktop-applications)

---

## Enhanced Perplexity CLI (v1.1)

**Status:** BETA

### Features

- Multi-turn conversations with persistent context
- Streaming responses for faster feedback
- Multiple output formats (Plain, Markdown, JSON, Shell, Auto)
- Automatic Mermaid diagram support for workflows/architecture
- Client-side syntax highlighting (bat/pygmentize)
- Save responses to Markdown files

### Installation

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Make script executable
chmod +x perplex_cli_v1.1.sh

# Run with API key (or set PERPLEXITY_API_KEY env var)
./perplex_cli_v1.1.sh <Your_API_Key>

# API key will be saved to ~/.perplexity_api_key on first run
```

### Requirements

- Perplexity API key (get from https://www.perplexity.ai/)
- **Recommended:** `jq`, `bat`, `fzf` for enhanced functionality
  ```bash
  sudo apt install -y jq bat fzf
  ```

### Usage

```bash
# Interactive mode (default)
./perplex_cli_v1.1.sh

# Pipe mode for automation
echo "Explain Docker networking" | ./perplex_cli_v1.1.sh --cli
```

### Interactive Commands

```
:help                 Show all commands
:exit                 Quit
:format <type>        Set format (Plain|Markdown|JSON|Shell|Auto)
:render <on|off>      Toggle client-side rendering
:stream <on|off>      Toggle streaming mode
:context <on|off>     Enable/disable conversation history
:history              View saved conversation context
:save <file>          Save last response to Markdown file
:clear                Clear the terminal
```

### Example Session

```
perplexity> :format Markdown
Format set: Markdown

perplexity> :context on
Context ON

perplexity> Explain the OSI model with a diagram
Enter multi-line input; end with a line containing only EOF
EOF

[Response with Mermaid diagram will be displayed]

perplexity> :save osi_model.md
Saved to osi_model.md
```

---

## Legacy Perplexity Script

```bash
# Navigate to ai_fun directory
cd ai_fun/

# Run with API key
./perplex.sh <Perplexity_API_Key>
```

**How it works:**
1. Enter your query when prompted
2. Type `EOF` on a new line to submit
3. Response rendered in markdown format
4. Option to export to `.md` file

---

## Python Desktop Applications

Desktop GUI versions are available in `ai_fun/python/` (v1.0-v1.4).

**Features:**
- GTK-based graphical interface
- Desktop integration with `.desktop` files
- Asset management for icons and resources
- Generated markdown file storage

**Location:**
```
ai_fun/python/
├── perplexity_desktop_v1.0.py
├── perplexity_desktop_v1.2.py
├── perplexity_desktop_v1.3.py
├── perplexity_desktop_v1.4.py
├── assets/
│   └── perplexity.desktop
└── generated_md_files/
```
