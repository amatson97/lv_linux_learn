#!/usr/bin/env bash
# Interactive Perplexity terminal client (Claude-like). Robust conditionals; no placeholder ellipses.
# Usage:
#   ./perplex.sh                # interactive
#   echo "hi" | ./perplex.sh --cli
#   ./perplex.sh <API_KEY>

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

API_URL="https://api.perplexity.ai/chat/completions"
KEY_FILE="${HOME}/.perplexity_api_key"
CONTEXT_FILE="${HOME}/.perplexity_context.json"
TMP_PAYLOAD="$(mktemp)"
TMP_RESPONSE="$(mktemp)"
MODEL="sonar-pro"
MAX_TOKENS=1000
TEMPERATURE=0.3

# Defaults
FORMAT="Plain"    # Plain | Markdown | JSON | Shell
RENDER_ON=1       # client-side render toggle (0/1)
USE_CONTEXT=0     # persist conversation context

cleanup() {
  rm -f "$TMP_PAYLOAD" "$TMP_RESPONSE"
}
trap cleanup EXIT

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_key() {
  # arg1 optional key passed in
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
    # trim whitespace
    API_KEY="${API_KEY//[$'\t\r\n ']}"
    if [ -n "$API_KEY" ]; then
      return 0
    fi
  fi
  # interactive prompt
  read -rp "Perplexity API key: " API_KEY
  if [ -z "$API_KEY" ]; then
    echo "No API key provided; aborting." >&2
    exit 1
  fi
  read -r -p "Save key to ${KEY_FILE}? (y/N): " yn
  case "$yn" in
    [Yy]* )
      printf '%s' "$API_KEY" > "$KEY_FILE"
      chmod 600 "$KEY_FILE"
      echo "Saved key to ${KEY_FILE}."
      ;;
    *) ;;
  esac
}

build_payload() {
  local prompt="$1"
  local system_instr
  system_instr="You are a helpful, concise assistant. Respond ONLY in the requested format. Requested format: ${FORMAT}."

  # Determine existing context safely
  existing='[]'
  if [ "${USE_CONTEXT:-0}" -eq 1 ]; then
    if [ -f "$CONTEXT_FILE" ]; then
      if command_exists jq; then
        if jq -e . >/dev/null 2>&1 < "$CONTEXT_FILE"; then
          existing="$(cat "$CONTEXT_FILE")"
        else
          existing='[]'
        fi
      else
        # jq missing: try to treat file content as raw JSON-ish; safest is to ignore
        existing='[]'
      fi
    fi
  fi

  # Use jq when available, else python3 fallback, else naive JSON escape
  if command_exists jq; then
    jq -n --argjson existing "$existing" \
      --arg system "$system_instr" \
      --arg user "$prompt" \
      --arg model "$MODEL" \
      --argjson max_tokens "$MAX_TOKENS" \
      --argjson temperature "$TEMPERATURE" \
      '
      ($existing // []) + [{role:"system", content:$system}, {role:"user", content:$user}]
      | {model:$model, messages:., max_tokens:$max_tokens, temperature:$temperature}
      ' > "$TMP_PAYLOAD"
    return 0
  fi

  if command_exists python3; then
    # Safely build using python3 to avoid malformed JSON
    python3 - "$existing" "$system_instr" "$prompt" "$MODEL" "$MAX_TOKENS" "$TEMPERATURE" <<'PY' > "$TMP_PAYLOAD"
import json,sys
existing = json.loads(sys.argv[1]) if sys.argv[1] and sys.argv[1] != '[]' else []
system = sys.argv[2]
user = sys.argv[3]
model = sys.argv[4]
max_tokens = int(sys.argv[5])
temperature = float(sys.argv[6])
payload = {
  "model": model,
  "messages": existing + [{"role":"system","content":system}, {"role":"user","content":user}],
  "max_tokens": max_tokens,
  "temperature": temperature
}
print(json.dumps(payload))
PY
    return 0
  fi

  # Last-resort naive construction (best-effort)
  esc_prompt="${prompt//\"/\\\"}"
  esc_system="${system_instr//\"/\\\"}"
  cat > "$TMP_PAYLOAD" <<EOF
{"model":"${MODEL}","messages":[{"role":"system","content":"${esc_system}"},{"role":"user","content":"${esc_prompt}"}],"max_tokens":${MAX_TOKENS},"temperature":${TEMPERATURE}}
EOF
}

append_context() {
  # $1 role, $2 content
  if [ "${USE_CONTEXT:-0}" -ne 1 ]; then return 0; fi
  local role="$1"; local content="$2"
  if [ -f "$CONTEXT_FILE" ]; then
    if command_exists jq && jq -e . >/dev/null 2>&1 < "$CONTEXT_FILE"; then
      jq --arg role "$role" --arg content "$content" '. + [{role:$role, content:$content}]' "$CONTEXT_FILE" > "${CONTEXT_FILE}.tmp" && mv "${CONTEXT_FILE}.tmp" "$CONTEXT_FILE"
      return 0
    fi
  fi
  # create new
  if command_exists jq; then
    jq -n --arg role "$role" --arg content "$content" '[{role:$role, content:$content}]' > "$CONTEXT_FILE"
  else
    printf '%s\n' "[{\"role\":\"$role\",\"content\":\"$content\"}]" > "$CONTEXT_FILE"
  fi
}

send_request() {
  if ! command_exists curl; then
    echo "curl is required but not installed." >&2
    return 1
  fi
  if ! curl -sS -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $API_KEY" \
      -d @"$TMP_PAYLOAD" \
      -o "$TMP_RESPONSE"; then
    echo "Request failed (network or curl error)." >&2
    return 2
  fi
  return 0
}

process_response() {
  local resp_file="$1"
  local content
  if command_exists jq; then
    content="$(jq -r '.choices[0].message.content // .choices[0].text // .text // empty' < "$resp_file" 2>/dev/null || true)"
  else
    # attempt crude extraction
    content="$(grep -oP '(?<="content"\s*:\s*")[^"]+' < "$resp_file" | head -n1 || true)"
  fi

  if [ -z "$content" ]; then
    echo "No content found in response. Raw response:"
    sed -n '1,200p' "$resp_file"
    return 1
  fi
  LAST_RESPONSE_RAW="$content"

  case "$FORMAT" in
    JSON)
      echo "=== JSON Response ==="
      if command_exists jq; then
        echo "$content" | jq .
      else
        echo "$content"
      fi
      ;;
    Markdown)
      echo "=== Markdown Response ==="
      if command_exists bat; then
        echo "$content" | bat --paging=always --style=plain --color=always -l markdown
      else
        printf '%s\n' "$content" | less -R
      fi
      ;;
    Shell)
      echo "=== Shell Response ==="
      if command_exists bat; then
        echo "$content" | bat --paging=always --style=plain --color=always -l sh
      else
        printf '%s\n' "$content" | less -R
      fi
      ;;
    Plain|*)
      echo "=== Response ==="
      printf '%s\n' "$content"
      ;;
  esac

  # citations if present
  if command_exists jq; then
    LAST_CITATIONS="$(jq -r '.citations[]?' < "$resp_file" 2>/dev/null | sed 's/^/- /' || true)"
  else
    LAST_CITATIONS=""
  fi
  if [ -n "${LAST_CITATIONS:-}" ]; then
    echo -e "\nCitations:\n$LAST_CITATIONS"
  fi

  append_context "assistant" "$content"
}

show_help() {
  cat <<'EOF'
Commands (type on a single line, starting with ':'):
  :help                  show this help
  :exit                  quit
  :format <Plain|Markdown|JSON|Shell>   set response format
  :render <on|off>       client-side render toggle (placeholder)
  :save <file.md>        save last prompt/response to Markdown file
  :context <on|off>      enable/disable persisted conversation context
  :history               show persistent context file (if enabled)
  :clear                 clear the terminal
Notes:
  - Start multi-line prompt with one line, finish entering lines and terminate with a line containing only EOF.
  - Non-interactive: echo "prompt" | ./perplex.sh --cli
EOF
}

interactive_loop() {
  echo "Perplexity interactive mode. Type :help for commands."
  while true; do
    printf "\nperplexity> "
    if ! IFS= read -r line; then
      echo "EOF on input; exiting."
      break
    fi

    case "$line" in
      :exit|:quit) echo "Bye."; break ;;
      :help) show_help; continue ;;
      :clear) clear; continue ;;
      :format*)
        arg="$(awk '{print $2}' <<< "$line" | tr -d '\r\n')"
        if [ -n "$arg" ]; then FORMAT="$arg"; echo "Format set to: $FORMAT"; else echo "Current format: $FORMAT"; fi
        continue
        ;;
      :render*)
        arg="$(awk '{print $2}' <<< "$line")"
        if [ "$arg" = "on" ]; then RENDER_ON=1; echo "Render ON"; else RENDER_ON=0; echo "Render OFF"; fi
        continue
        ;;
      :save*)
        file="$(awk '{print $2}' <<< "$line")"
        if [ -z "$file" ]; then echo "Usage: :save filename.md"; else
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
          echo "Saved to $file"
        fi
        continue
        ;;
      :context*)
        arg="$(awk '{print $2}' <<< "$line")"
        if [ "$arg" = "on" ]; then USE_CONTEXT=1; echo "Context ON"; elif [ "$arg" = "off" ]; then USE_CONTEXT=0; echo "Context OFF"; else echo "Usage: :context on|off"; fi
        continue
        ;;
      :history)
        if [ -f "$CONTEXT_FILE" ]; then
          echo "=== Context file: $CONTEXT_FILE ==="
          if command_exists jq; then jq . "$CONTEXT_FILE" || cat "$CONTEXT_FILE"; else cat "$CONTEXT_FILE"; fi
        else
          echo "No context file."
        fi
        continue
        ;;
      :)
        continue
        ;;
    esac

    # Read multi-line prompt until EOF sentinel
    if [ -z "$line" ]; then
      echo "Empty prompt; skip."
      continue
    fi

    echo "Enter multi-line input; end with a line containing only EOF"
    PROMPT="$line"
    while IFS= read -r sub; do
      if [ "$sub" = "EOF" ]; then break; fi
      PROMPT="$PROMPT"$'\n'"$sub"
    done

    LAST_PROMPT="$PROMPT"
    append_context "user" "$PROMPT"
    build_payload "$PROMPT"
    if ! send_request; then
      echo "Request failed; skipping."
      continue
    fi
    process_response "$TMP_RESPONSE"
  done
}

cli_pipe_mode() {
  PROMPT="$(cat -)"
  if [ -z "$PROMPT" ]; then echo "No prompt provided on stdin."; exit 1; fi
  LAST_PROMPT="$PROMPT"
  append_context "user" "$PROMPT"
  build_payload "$PROMPT"
  send_request || exit 2
  process_response "$TMP_RESPONSE"
}

main() {
  for dep in jq curl; do
    if ! command_exists "$dep"; then
      echo "Warning: recommended dependency '$dep' is missing." >&2
    fi
  done

  if [ "${1:-}" = "--cli" ]; then
    ensure_key ""
    if [ -t 0 ]; then
      echo "Use --cli with piped input. Example: echo 'hello' | $0 --cli" >&2
      exit 1
    fi
    cli_pipe_mode
    exit $?
  fi

  if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then show_help; exit 0; fi

  if [ -n "${1:-}" ]; then
    ensure_key "$1"
  else
    ensure_key ""
  fi

  interactive_loop
}

main "$@"