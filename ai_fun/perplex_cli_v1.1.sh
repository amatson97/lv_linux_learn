#!/usr/bin/env bash
# Interactive Perplexity terminal client (Claude-like). Enhanced.
# Usage:
#   ./perplex_cli_v1.1.sh            # interactive
#   echo "hi" | ./perplex_cli_v1.1.sh --cli
#   ./perplex_cli_v1.1.sh <API_KEY>

set -euo pipefail

# Ensure running under bash
if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  else
    echo "This script requires bash. Install bash and rerun." >&2
    exit 1
  fi
fi

# repo-aware helpers
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
if [ -f "$repo_root/includes/main.sh" ]; then
  # shellcheck source=/dev/null
  source "$repo_root/includes/main.sh"
else
  green_echo() { printf '\033[1;32m%s\033[0m\n' "$*"; }
fi

# Configuration
API_URL="https://api.perplexity.ai/chat/completions"
KEY_FILE="${HOME}/.perplexity_api_key"
CONTEXT_FILE="${HOME}/.perplexity_context.json"
TMP_PAYLOAD="$(mktemp)"
TMP_RESPONSE="$(mktemp)"
MODEL="sonar-pro"
MAX_TOKENS=1000
TEMPERATURE=0.3

# State variables
FORMAT="Plain"    # Plain | Markdown | JSON | Shell | Auto
RENDER_ON=1       # client-side render toggle (0/1)
USE_CONTEXT=0     # persist conversation context
CONTEXT_KEEP=12   # how many messages to keep
STREAMING=0       # streaming toggle (0/1)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

cleanup() {
  rm -f "$TMP_PAYLOAD" "$TMP_RESPONSE"
}
trap cleanup EXIT

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Log a status message with context
log_info() {
  green_echo "[INFO] $*"
}

log_error() {
  printf '\033[1;31m%s\033[0m\n' "[ERROR] $*" >&2
}

# ============================================================================
# COLORIZED OUTPUT & FORMATTING
# ============================================================================

# Colorized printing, uses bat -> pygmentize -> jq -> less
colorize_print() {
  local fmt="$1"; shift
  local text="$*"

  # Detect fenced code language if present
  local detected_lang=""
  if printf '%s\n' "$text" | grep -Eo '```[A-Za-z0-9_+-]+' >/dev/null 2>&1; then
    detected_lang=$(printf '%s\n' "$text" | grep -Eo '```[A-Za-z0-9_+-]+' | head -n1 | sed 's/^```//')
  fi

  local lang="text"
  if [ -n "$detected_lang" ]; then
    lang="$detected_lang"
  else
    case "$fmt" in
      JSON) lang="json" ;;
      Markdown) lang="markdown" ;;
      Shell) lang="sh" ;;
      *) lang="text" ;;
    esac
  fi

  # Prefer bat (color + paging), fallback to pygmentize, then jq, then less
  if command_exists bat; then
    printf '%s\n' "$text" | bat --paging=never --color=always -l "$lang" 2>/dev/null | less -R
    return
  fi

  if command_exists pygmentize; then
    printf '%s\n' "$text" | pygmentize -l "$lang" -f terminal256 -O style=native 2>/dev/null | less -R
    return
  fi

  if [ "$fmt" = "JSON" ] && command_exists jq; then
    printf '%s\n' "$text" | jq . 2>/dev/null | less -R
    return
  fi

  # Fallback: raw pager
  printf '%s\n' "$text" | less -R
}

# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

# Trim persisted context to avoid oversized payloads
defensive_trim_context() {
  if [ ! -f "$CONTEXT_FILE" ]; then return; fi
  if command_exists jq; then
    jq ".[-${CONTEXT_KEEP}:]" "$CONTEXT_FILE" > "${CONTEXT_FILE}.tmp" && mv "${CONTEXT_FILE}.tmp" "$CONTEXT_FILE" || true
  fi
}

# Validate and sanitize context file before sending to API
sanitize_existing_context_for_payload() {
  if [ ! -f "$CONTEXT_FILE" ]; then
    printf '%s' '[]'
    return 0
  fi

  # Use jq if available to safely parse and sanitize
  if command_exists jq && jq -e . >/dev/null 2>&1 < "$CONTEXT_FILE"; then
    # Remove trailing user message if present (avoid consecutive user messages)
    jq 'if (length>0 and .[-1].role=="user") then .[0:(length-1)] else . end' "$CONTEXT_FILE"
    return 0
  fi

  # Fallback to python3 parsing
  if command_exists python3; then
    python3 - <<PY "$(cat "$CONTEXT_FILE" 2>/dev/null || echo '[]')"
import sys, json
try:
    arr = json.loads(sys.argv[1])
    if isinstance(arr, list) and len(arr) > 0 and arr[-1].get("role") == "user":
        arr = arr[:-1]
    print(json.dumps(arr))
except Exception:
    print("[]")
PY
    return 0
  fi

  # Conservative fallback: return empty context
  printf '%s' '[]'
}

# Persist a message into the context file
append_context() {
  if [ "${USE_CONTEXT:-0}" -ne 1 ]; then return 0; fi
  local role="$1"; local content="$2"

  if [ -f "$CONTEXT_FILE" ]; then
    if command_exists jq && jq -e . >/dev/null 2>&1 < "$CONTEXT_FILE"; then
      jq --arg role "$role" --arg content "$content" '. + [{role:$role, content:$content}]' "$CONTEXT_FILE" > "${CONTEXT_FILE}.tmp" && mv "${CONTEXT_FILE}.tmp" "$CONTEXT_FILE"
    else
      # Corrupted file: recreate with single entry
      printf '[{"role":"%s","content":"%s"}]\n' "$role" "${content//\"/\\\"}" > "$CONTEXT_FILE"
    fi
  else
    # Create new context file
    printf '[{"role":"%s","content":"%s"}]\n' "$role" "${content//\"/\\\"}" > "$CONTEXT_FILE"
  fi

  defensive_trim_context
}

# ============================================================================
# TEXT EXTRACTION & PARSING
# ============================================================================

# Extract JSON block from response text
extract_json_from_text() {
  local text="$1"
  if [ -z "$text" ]; then
    printf ''
    return 0
  fi

  # Try fenced ```json block
  if printf '%s\n' "$text" | sed -n '/```json/,/```/p' | sed '1d;$d' | grep -q '[^[:space:]]'; then
    printf '%s\n' "$text" | sed -n '/```json/,/```/p' | sed '1d;$d'
    return 0
  fi

  # Try any fence containing { ... }
  if printf '%s\n' "$text" | sed -n '/```/,/```/p' | sed '1d;$d' | grep -q '{'; then
    printf '%s\n' "$text" | sed -n '/```/,/```/p' | sed '1d;$d' | sed -n '1,400p'
    return 0
  fi

  # Use python3 to extract first balanced {...} JSON object
  if command_exists python3; then
    printf '%s' "$text" | python3 - <<'PY'
import sys, re, json
s = sys.stdin.read()
m = re.search(r'```json\s*(.*?)\s*```', s, re.S)
if m:
    print(m.group(1))
    sys.exit(0)
start = s.find('{')
if start == -1:
    sys.exit(0)
cnt = 0
for i in range(start, len(s)):
    if s[i] == '{':
        cnt += 1
    elif s[i] == '}':
        cnt -= 1
        if cnt == 0:
            candidate = s[start:i+1]
            try:
                json.loads(candidate)
                print(candidate)
            except:
                pass
            break
PY
    return 0
  fi

  printf ''
}

# Extract code block from response text (bash/shell preferred)
extract_code_from_text() {
  local text="$1"

  # Try bash/sh fenced blocks
  if printf '%s\n' "$text" | sed -n '/```\(bash\|sh\)\?/,/```/p' | sed '1d;$d' | grep -q '[^[:space:]]'; then
    printf '%s\n' "$text" | sed -n '/```\(bash\|sh\)\?/,/```/p' | sed '1d;$d'
    return 0
  fi

  # Try any code fence
  if printf '%s\n' "$text" | sed -n '/```/,/```/p' | sed '1d;$d' | grep -q '[^[:space:]]'; then
    printf '%s\n' "$text" | sed -n '/```/,/```/p' | sed '1d;$d'
    return 0
  fi

  # Extract shell-like commands (lines starting with $ or common shell tokens)
  printf '%s\n' "$text" | awk '/^\$ /{sub(/^\$ /,""); print; next} /^[a-z0-9_\-]+ .*$/ {print}' | sed -n '1,200p'
}

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

ensure_key() {
  if [ -n "${1:-}" ]; then
    API_KEY="$1"
    return 0
  fi
  if [ -n "${PERPLEXITY_API_KEY:-}" ]; then
    API_KEY="${PERPLEXITY_API_KEY}"
    return 0
  fi
  if [ -f "$KEY_FILE" ]; then
    API_KEY="$(<"$KEY_FILE")"
    API_KEY="${API_KEY//[$'\t\r\n ']}"
    if [ -n "$API_KEY" ]; then return 0; fi
  fi

  # Interactive prompt
  read -rp "Perplexity API key: " API_KEY
  if [ -z "$API_KEY" ]; then
    log_error "No API key provided; aborting."
    exit 1
  fi

  read -r -p "Save key to ${KEY_FILE}? (y/N): " yn
  case "$yn" in
    [Yy]*)
      printf '%s' "$API_KEY" > "$KEY_FILE"
      chmod 600 "$KEY_FILE"
      log_info "Saved key to ${KEY_FILE}."
      ;;
    *)
      ;;
  esac
}

# ============================================================================
# PAYLOAD CONSTRUCTION
# ============================================================================

build_payload() {
  local prompt="$1"
  local system_instr="You are a helpful, concise assistant. Respond ONLY in the requested format. Requested format: ${FORMAT}."

  if [ "${FORMAT}" = "JSON" ]; then
    system_instr="${system_instr} If JSON is requested, return a single JSON object or array or wrap valid JSON in triple backticks with language 'json'. Do not include additional prose."
  fi

  # Safely determine and sanitize existing context
  local existing='[]'
  if [ "${USE_CONTEXT:-0}" -eq 1 ]; then
    existing="$(sanitize_existing_context_for_payload || printf '[]')"
  fi

  # Build payload using jq (preferred), python3 fallback, or naive JSON
  if command_exists jq; then
    jq -n \
      --argjson existing "$existing" \
      --arg system "$system_instr" \
      --arg user "$prompt" \
      --arg model "$MODEL" \
      --argjson max_tokens "$MAX_TOKENS" \
      --argjson temperature "$TEMPERATURE" \
      '($existing // []) + [{role:"system", content:$system},{role:"user",content:$user}] | {model:$model,messages:.,max_tokens:$max_tokens,temperature:$temperature}' > "$TMP_PAYLOAD"
    return 0
  fi

  if command_exists python3; then
    python3 - "$existing" "$system_instr" "$prompt" "$MODEL" "$MAX_TOKENS" "$TEMPERATURE" <<'PY' > "$TMP_PAYLOAD"
import json, sys
existing = json.loads(sys.argv[1]) if sys.argv[1] and sys.argv[1] != '[]' else []
system = sys.argv[2]
user = sys.argv[3]
model = sys.argv[4]
max_tokens = int(sys.argv[5])
temperature = float(sys.argv[6])
payload = {
    "model": model,
    "messages": existing + [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ],
    "max_tokens": max_tokens,
    "temperature": temperature
}
print(json.dumps(payload))
PY
    return 0
  fi

  # Naive JSON construction (last resort)
  local esc_prompt="${prompt//\"/\\\"}"
  local esc_system="${system_instr//\"/\\\"}"
  cat > "$TMP_PAYLOAD" <<EOF
{"model":"${MODEL}","messages":[{"role":"system","content":"${esc_system}"},{"role":"user","content":"${esc_prompt}"}],"max_tokens":${MAX_TOKENS},"temperature":${TEMPERATURE}}
EOF
}

# ============================================================================
# API REQUESTS
# ============================================================================

send_request() {
  if ! command_exists curl; then
    log_error "curl is required but not installed."
    return 1
  fi

  if ! curl -sS -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d @"$TMP_PAYLOAD" \
    -o "$TMP_RESPONSE"; then
    log_error "Request failed (curl error)"
    return 2
  fi
  return 0
}

# Streaming request: prints incremental content and assembles into TMP_RESPONSE
send_request_stream() {
  if ! command_exists curl; then
    log_error "curl is required for streaming."
    return 1
  fi

  local assm_content=""

  # Use -N/--no-buffer for immediate output flushing
  curl -sS -N -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_KEY" \
    -d @"$TMP_PAYLOAD" | while IFS= read -r line || [ -n "$line" ]; do

    local chunk="$line"
    # Handle SSE format: "data: {...}"
    if [[ "$line" =~ ^data:\ (.*) ]]; then
      chunk="${BASH_REMATCH[1]}"
    fi

    # Skip empty lines or completion markers
    if [[ -z "$chunk" || "$chunk" = "[DONE]" ]]; then
      continue
    fi

    # Extract text from common response shapes
    local text_piece=""
    if command_exists jq; then
      text_piece=$(printf '%s\n' "$chunk" | jq -r '.choices[0].delta.content // .choices[0].message.content // .choices[0].text // .text // empty' 2>/dev/null || true)
    else
      text_piece=$(printf '%s\n' "$chunk" | sed -n 's/.*"content":[[:space:]]*"\([^"]*\)".*/\1/p' || true)
    fi

    if [ -n "$text_piece" ]; then
      printf '%s' "$text_piece"
      assm_content+="$text_piece"
      # Flush stdout
      printf '' >&1
    fi
  done

  printf '\n'

  # Assemble final response JSON using python or naive escape
  if command_exists python3; then
    printf '%s' "$assm_content" | python3 - <<'PY' > "$TMP_RESPONSE"
import sys, json
content = sys.stdin.read()
print(json.dumps({"choices": [{"message": {"content": content}}]}))
PY
  else
    local esc="${assm_content//\"/\\\"}"
    printf '{"choices":[{"message":{"content":"%s"}}]}\n' "$esc" > "$TMP_RESPONSE"
  fi
  return 0
}

# ============================================================================
# RESPONSE PROCESSING
# ============================================================================

process_response() {
  local resp_file="$1"
  local raw=""

  # Extract content from response
  if command_exists jq; then
    raw="$(jq -r '.choices[0].message.content // .choices[0].text // .text // empty' < "$resp_file" 2>/dev/null || true)"
  else
    raw="$(sed -n '1,400p' "$resp_file")"
  fi

  if [ -z "$raw" ]; then
    log_error "No content in response."
    echo "Raw response:"
    sed -n '1,200p' "$resp_file"
    return 1
  fi

  LAST_RESPONSE_RAW="$raw"

  # Auto-detect format if requested
  local use_fmt="$FORMAT"
  if [ "$FORMAT" = "Auto" ]; then
    if extract_json_from_text "$raw" | grep -q '[{}\[]' >/dev/null 2>&1; then
      use_fmt="JSON"
    elif extract_code_from_text "$raw" | grep -q '[^[:space:]]' >/dev/null 2>&1; then
      use_fmt="Shell"
    else
      use_fmt="Markdown"
    fi
  fi

  # Display response according to format
  case "$use_fmt" in
    JSON)
      local json_block
      json_block="$(extract_json_from_text "$raw")"
      if [ -n "$json_block" ]; then
        if command_exists jq && printf '%s' "$json_block" | jq . >/dev/null 2>&1; then
          green_echo "=== JSON (extracted) ==="
          colorize_print JSON "$json_block"
        else
          green_echo "=== JSON (raw) ==="
          colorize_print JSON "$json_block"
        fi
      else
        if command_exists jq && printf '%s' "$raw" | jq . >/dev/null 2>&1; then
          green_echo "=== JSON ==="
          colorize_print JSON "$raw"
        else
          echo "=== Response (not valid JSON) ==="
          colorize_print Plain "$raw"
        fi
      fi
      ;;
    Markdown)
      green_echo "=== Markdown ==="
      if [ "$RENDER_ON" -eq 1 ]; then
        colorize_print Markdown "$raw"
      else
        printf '%s\n' "$raw"
      fi
      ;;
    Shell)
      green_echo "=== Shell ==="
      local code
      code="$(extract_code_from_text "$raw")"
      if [ -n "$code" ]; then
        colorize_print Shell "$code"
      else
        colorize_print Shell "$raw"
      fi
      ;;
    Plain|*)
      green_echo "=== Response ==="
      printf '%s\n' "$raw"
      ;;
  esac

  # Display citations if present
  if command_exists jq; then
    LAST_CITATIONS="$(jq -r '.citations[]?' < "$resp_file" 2>/dev/null | sed 's/^/- /' || true)"
  else
    LAST_CITATIONS=""
  fi
  if [ -n "${LAST_CITATIONS:-}" ]; then
    printf '\References:\n%s\n' "$LAST_CITATIONS"
  fi

  # Persist assistant's response into context
  append_context "assistant" "$raw"
}

# ============================================================================
# INTERACTIVE UI
# ============================================================================

show_help() {
  cat <<'EOF'
Commands (start with ':'):
  :help                 show help
  :exit                 quit
  :format <Plain|Markdown|JSON|Shell|Auto>  choose response format
  :render <on|off>      toggle client-side rendering
  :stream <on|off>      toggle streaming mode
  :save <file>          save last response to Markdown file (opens $EDITOR if set)
  :context <on|off>     toggle persistent conversation context
  :history              show saved conversation context
  :clear                clear the terminal

Examples:
  :format JSON          format responses as JSON
  :context on           enable persistent multi-turn conversation
  :save response.md     save last response to file
  :stream on            enable streaming output (faster feedback)
EOF
}

interactive_loop() {
  log_info "Perplexity interactive mode. Type :help for commands. End multi-line input with EOF on its own line."
  while true; do
    printf "\nperplexity> "
    if ! IFS= read -r line; then
      echo "EOF; exiting."
      break
    fi

    case "$line" in
      :exit|:quit)
        echo "Bye."
        break
        ;;
      :help)
        show_help
        continue
        ;;
      :clear)
        clear
        continue
        ;;
      :format*)
        local arg
        arg="$(awk '{print $2}' <<< "$line" | tr -d '\r\n')"
        if [ -n "$arg" ]; then
          FORMAT="$arg"
          log_info "Format set: $FORMAT"
        else
          echo "Current format: $FORMAT"
        fi
        continue
        ;;
      :render*)
        local arg
        arg="$(awk '{print $2}' <<< "$line")"
        if [ "$arg" = "on" ]; then
          RENDER_ON=1
          log_info "Render ON"
        else
          RENDER_ON=0
          log_info "Render OFF"
        fi
        continue
        ;;
      :stream*)
        local arg
        arg="$(awk '{print $2}' <<< "$line")"
        if [ "$arg" = "on" ]; then
          STREAMING=1
          log_info "Streaming ON"
        else
          STREAMING=0
          log_info "Streaming OFF"
        fi
        continue
        ;;
      :save*)
        local file
        file="$(awk '{print $2}' <<< "$line")"
        if [ -z "$file" ]; then
          echo "Usage: :save filename.md"
        else
          {
            echo "# Perplexity API Response"
            echo
            echo "## Prompt"
            echo '```'
            printf '%s\n' "$LAST_PROMPT"
            echo '```'
            echo
            echo "## Response"
            printf '%s\n' "$LAST_RESPONSE_RAW"
            if [ -n "${LAST_CITATIONS:-}" ]; then
              echo
              echo "## Citations"
              printf '%s\n' "$LAST_CITATIONS"
            fi
          } > "$file"
          log_info "Saved to $file"
          if [ -n "${EDITOR:-}" ] && command_exists "$EDITOR"; then
            "$EDITOR" "$file" &
          fi
        fi
        continue
        ;;
      :context*)
        local arg
        arg="$(awk '{print $2}' <<< "$line")"
        if [ "$arg" = "on" ]; then
          USE_CONTEXT=1
          log_info "Context ON"
        elif [ "$arg" = "off" ]; then
          USE_CONTEXT=0
          log_info "Context OFF"
        else
          echo "Usage: :context on|off"
        fi
        continue
        ;;
      :history)
        if [ -f "$CONTEXT_FILE" ]; then
          echo "=== Conversation Context: $CONTEXT_FILE ==="
          if command_exists jq; then
            jq . "$CONTEXT_FILE" || cat "$CONTEXT_FILE"
          else
            cat "$CONTEXT_FILE"
          fi
        else
          echo "No context file."
        fi
        continue
        ;;
      :)
        continue
        ;;
    esac

    # Validate non-command input
    if [ -z "$line" ]; then
      echo "Empty prompt; skipping."
      continue
    fi

    # Read multi-line prompt until EOF sentinel
    echo "Enter multi-line input; end with a line containing only EOF"
    PROMPT="$line"
    while IFS= read -r sub; do
      [ "$sub" = "EOF" ] && break
      PROMPT="$PROMPT"$'\n'"$sub"
    done

    LAST_PROMPT="$PROMPT"
    build_payload "$PROMPT"

    # Send request (with streaming fallback if enabled)
    if [ "${STREAMING:-0}" -eq 1 ]; then
      if ! send_request_stream; then
        log_info "Streaming failed; falling back to normal request."
        if ! send_request; then
          log_error "Request failed; skipping."
          continue
        fi
      fi
    else
      if ! send_request; then
        log_error "Request failed; skipping."
        continue
      fi
    fi

    # Persist user message and process response
    append_context "user" "$PROMPT"
    process_response "$TMP_RESPONSE"
  done
}

# Pipe mode: read prompt from stdin
cli_pipe_mode() {
  PROMPT="$(cat -)"
  if [ -z "$PROMPT" ]; then
    log_error "No prompt provided on stdin."
    exit 1
  fi

  LAST_PROMPT="$PROMPT"
  build_payload "$PROMPT"

  if [ "${STREAMING:-0}" -eq 1 ]; then
    send_request_stream || send_request || exit 2
  else
    send_request || exit 2
  fi

  append_context "user" "$PROMPT"
  process_response "$TMP_RESPONSE"
}

# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================

main() {
  # Warn about missing dependencies
  for dep in jq curl; do
    if ! command_exists "$dep"; then
      log_error "Recommended dependency '$dep' is missing."
    fi
  done

  # Handle CLI pipe mode
  if [ "${1:-}" = "--cli" ]; then
    ensure_key ""
    if [ -t 0 ]; then
      log_error "Use --cli with piped input. Example: echo 'hello' | $0 --cli"
      exit 1
    fi
    cli_pipe_mode
    exit $?
  fi

  # Handle help
  if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    show_help
    exit 0
  fi

  # Ensure API key is available
  if [ -n "${1:-}" ]; then
    ensure_key "$1"
  else
    ensure_key ""
  fi

  # Enter interactive mode
  interactive_loop
}

main "$@"