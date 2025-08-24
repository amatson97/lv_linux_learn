#!/bin/bash

API_KEY="${PERPLEXITY_API_KEY:-your_perplexity_api_key_here}"

echo "Paste your code or question. Type EOF on a new line when done."

INPUT=""
while IFS= read -r line; do
  [[ $line == "EOF" ]] && break
  INPUT+="$line\n"
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
  # Sanitize filename from user prompt, default if empty
  filename="perplexity_response_$(date +%Y%m%d_%H%M%S).md"

  # Prepare Markdown content
  md_content="# Perplexity API Response\n\n"
  md_content+="## Prompt\n"
  md_content+="``````\n\n"
  md_content+="## Response\n"
  md_content+="``````\n\n"

  if [[ -n "$CITATIONS" ]]; then
    md_content+="## Citations\n"
    # Convert bullets to markdown list
    md_content+=$(echo "$CITATIONS" | sed 's/^/- /')
    md_content+="\n"
  fi

  # Write to file
  echo -e "$md_content" > "$filename"
  echo "Response saved to $filename"
fi