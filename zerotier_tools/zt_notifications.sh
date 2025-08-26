#!/bin/bash
# * * * * * DISPLAY=:0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus /home/adam/lv_linux_learn/zerotier_tools/zt_notifications.sh ApT2ayFbk2uxhPBpG2bZSWewfcbjqFSe 8bd5124fd60a971f
# Usage: ./zt_notifications.sh API_TOKEN NETWORK_ID

API_TOKEN="$1"
NETWORK_ID="$2"
KNOWN_NODES_FILE="$HOME/.zerotier_known_nodes"

if [[ -z "$API_TOKEN" || -z "$NETWORK_ID" ]]; then
  echo "Usage: $0 API_TOKEN NETWORK_ID"
  exit 1
fi

# Fetch current network members from ZeroTier API
response=$(curl -s -H "Authorization: token $API_TOKEN" \
  "https://my.zerotier.com/api/v1/network/$NETWORK_ID/member")
if [[ -z "$response" ]]; then
  echo "No response from API"
  exit 2
fi

# Initialize known nodes file if missing
if [ ! -f "$KNOWN_NODES_FILE" ]; then
  touch "$KNOWN_NODES_FILE"
fi

# Current and previous nodes as arrays
mapfile -t current_nodes < <(echo "$response" | jq -r '.[].nodeId // .[].id')
mapfile -t known_nodes < "$KNOWN_NODES_FILE"

# Convert arrays to associative arrays for quick lookup
declare -A current_map=()
declare -A known_map=()

for node in "${current_nodes[@]}"; do
  current_map["$node"]=1
done
for node in "${known_nodes[@]}"; do
  known_map["$node"]=1
done

# Detect added and removed nodes
added_nodes=()
removed_nodes=()

for node in "${current_nodes[@]}"; do
  if [[ -z "${known_map[$node]}" ]]; then
    added_nodes+=("$node")
  fi
done

for node in "${known_nodes[@]}"; do
  if [[ -z "${current_map[$node]}" ]]; then
    removed_nodes+=("$node")
  fi
done

# Notify for added nodes
for node in "${added_nodes[@]}"; do
  node_name=$(echo "$response" | jq -r ".[] | select(.nodeId==\"$node\" or .id==\"$node\") | .name // .description // \"(no name)\"")
  notify-send "ZeroTier Alert" "Node joined: $node_name ($node)"
done

# Notify for removed nodes
for node in "${removed_nodes[@]}"; do
  # For removed nodes, we no longer have data from API, so just notify by node ID
  notify-send "ZeroTier Alert" "Node left: $node"
done

# Save current nodes to known nodes file
printf "%s\n" "${current_nodes[@]}" > "$KNOWN_NODES_FILE"