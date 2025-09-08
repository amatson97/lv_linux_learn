#!/bin/bash
# Usage: ./zt_members_table.sh <api_token> <network_id>
# Or you can replace the curl part with your get_ip.sh output if local JSON file
# It will render to terminal in text

API_TOKEN="$1"
NETWORK_ID="$2"
HTML_FILE="${3:-zerotier_members.html}"

if [[ -z "$API_TOKEN" || -z "$NETWORK_ID" ]]; then
  echo "Usage: $0 <API_TOKEN> <NETWORK_ID> [output_html_file]"
  exit 1
fi

# Fetch JSON from ZeroTier API
response=$(curl -s -H "Authorization: token $API_TOKEN" \
  "https://my.zerotier.com/api/v1/network/$NETWORK_ID/member")

if [[ -z "$response" ]]; then
  echo "No response from API"
  exit 2
fi


print_table() {
  printf "%-22s\t%-20s\t%-20s\t%-8s\n" "NODE ID" "NAME/DESCRIPTION" "MANAGED IP(S)" "STATUS"
  printf '%*s\n' 75 '' | tr ' ' '-'
  threshold_ms=$(( $(date +%s) * 1000 - 300000 ))
  
  echo "$response" | jq -r --argjson threshold "$threshold_ms" '
    .[] |
    {
      nodeId: (.nodeId // .id // ""),
      name: (.name // .description // ""),
      ips: (.config.ipAssignments // .config.assignedAddresses // [] | join(", ")),
      status: (if (.lastSeen != null and .lastSeen > $threshold) then "Online" else "Offline" end)
    } |
    [ .nodeId, .name, .ips, .status ] | @tsv' | column -t -s $'\t'
}

print_table