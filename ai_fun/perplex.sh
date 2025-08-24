#!/bin/bash

API_KEY="$1"

# Check if API key was provided on command line
if [[ -z "$API_KEY" ]]; then
  echo "Usage: $0 <Perplexity API Key>"
  exit 1
fi

echo "Paste your code or question. Type EOF on a new line when done."

# Read multi-line input, appending real newlines
INPUT=""
while IFS= read -r line; do
  [[ $line == "EOF" ]] && break
  INPUT+="$line"$'\n'
done

# Compose JSON payload with escaped input
JSON_PAYLOAD=$(jq -c -n --arg model "sonar-pro" --arg content "$INPUT" \
  '{
    model: $model,
    messages: [{
      role: "user",
      content: $content
    }],
    max_tokens: 1000,
    temperature: 0.3
  }')

echo -e "\n\e[1;34mJSON Payload to be sent:\e[0m"
echo "$JSON_PAYLOAD" | jq '.'

# Send POST request to Perplexity API
RESPONSE=$(curl -s -X POST "https://api.perplexity.ai/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "$JSON_PAYLOAD")

# Extract main response content, folded at 80 chars for terminal display
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // "No content in response."' | fold -s -w 80)

# Extract citations if available
CITATIONS=$(echo "$RESPONSE" | jq -r '.citations[]?' | sed 's/^/- /')

# Pretty print response in the terminal
echo -e "\n\e[1;34m===== Perplexity API Response =====\e[0m\n"
printf "%s\n\n" "$CONTENT"

if [[ -n "$CITATIONS" ]]; then
  echo -e "\e[1;33mCitations:\e[0m"
  echo "$CITATIONS"
fi

echo -e "\n\e[1;34m==================================\e[0m\n"

# Prompt user to save as Markdown file
read -p "Save response as Markdown file? (y/n): " save_md
if [[ "$save_md" =~ ^[Yy]$ ]]; then
  filename="perplexity_response_$(date +%Y%m%d_%H%M%S).md"
  {
    echo "# Perplexity API Response"
    echo
    echo "## Prompt"
    echo '```'
    printf '%s\n' "$INPUT"
    echo '```'
    echo
    echo "## Response"
    echo '```'
    printf '%s\n' "$CONTENT"
    echo '```'
    if [[ -n "$CITATIONS" ]]; then
      echo
      echo "## Citations"
      echo "$CITATIONS"
    fi
  } > "$filename"
  echo "Response saved to $filename"
fi