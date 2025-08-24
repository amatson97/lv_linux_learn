#!/bin/bash
# Usage: ./zt_members_table.sh <api_token> <network_id>
# Or you can replace the curl part with your get_ip.sh output if local JSON file
# It will render to terminal in text

API_TOKEN="$1"
NETWORK_ID="$2"

if [[ -z "$API_TOKEN" || -z "$NETWORK_ID" ]]; then
  echo "Usage: $0 <API_TOKEN> <NETWORK_ID>"
  exit 1
fi

# Fetch the JSON data from the API
response=$(curl -s -H "Authorization: token $API_TOKEN" \
  "https://my.zerotier.com/api/v1/network/$NETWORK_ID/member")

if [[ -z "$response" ]]; then
  echo "No response from API"
  exit 2
fi

# Print table header
printf "%-22s  %-20s  %-20s  %-8s\n" "NODE ID" "NAME/DESCRIPTION" "MANAGED IP(S)" "STATUS"
printf '%*s\n' 75 '' | tr ' ' '-'

# Iterate over each member, decode base64 JSON for safety with jq
echo "$response" | jq -c '.[]' | while read -r member; do
  nodeId=$(echo "$member" | jq -r '.nodeId // .id // empty')
  name=$(echo "$member" | jq -r '.name // .description // ""')
  ips=$(echo "$member" | jq -r '.config.ipAssignments // .config.assignedAddresses // [] | join(", ")')
  online=$(echo "$member" | jq -r '.online // false')
  status="Offline"
  [[ "$online" == "true" ]] && status="Online"

  printf "%-22s  %-20s  %-20s  %-8s\n" "$nodeId" "$name" "$ips" "$status"
done