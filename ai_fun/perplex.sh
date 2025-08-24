#!/bin/bash

API_KEY="${PERPLEXITY_API_KEY:-your_perplexity_api_key_here}"

echo "Paste your code or question. Type EOF on a new line when done."

INPUT=""
while IFS= read -r line; do
  [[ $line == "EOF" ]] && break
  INPUT+="$line"$'\n'  # Append actual newline character
done

# Compose JSON payload correctly using jq
JSON_PAYLOAD=$(jq -c -n --arg model "sonar-pro" --arg content "$INPUT" \
  '{
    model: $model,
    messages: [
      {
        role: "user",
        content: $content
      }
    ],
    max_tokens: 1000,
    temperature: 0.3
  }')

echo -e "\n\e[1;34mJSON Payload to be sent:\e[0m"
echo "$JSON_PAYLOAD" | jq '.'  # Pretty print JSON payload

# Send request
RESPONSE=$(curl -s -X POST "https://api.perplexity.ai/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "$JSON_PAYLOAD")

# Extract main message content and wrap lines at 80 chars for terminal output
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // "No content in response."' | fold -s -w 80)

# Extract citations if present
CITATIONS=$(echo "$RESPONSE" | jq -r '.citations[]?' | sed 's/^/- /')

# Terminal pretty print with colors and spacing
echo -e "\n\e[1;34m===== Perplexity API Response =====\e[0m\n"
printf "%s\n\n" "$CONTENT"

if [[ -n "$CITATIONS" ]]; then
  echo -e "\e[1;33mCitations:\e[0m"
  echo "$CITATIONS"
fi

echo -e "\n\e[1;34m==================================\e[0m\n"

# Ask user if they want to save the response as Markdown
read -p "Save response as Markdown file? (y/n): " save_md
if [[ "$save_md" =~ ^[Yy]$ ]]; then
  filename="perplexity_response_$(date +%Y%m%d_%H%M%S).md"

  # Prepare Markdown content with proper newlines
  {
    echo "# Perplexity API Response"
    echo
    echo "## Prompt"
    echo '```
    printf '%s\n' "$INPUT"
    echo '```'
    echo
    echo "## Response"
    echo '```
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