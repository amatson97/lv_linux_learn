#!/bin/bash
# Usage: ./zt_notifications.sh API_TOKEN NETWORK_ID

API_TOKEN="$1"
NETWORK_ID="$2"
KNOWN_NODES_FILE="$HOME/.zerotier_known_nodes"
KNOWN_ONLINE_FILE="$HOME/.zerotier_known_online_nodes"
ONLINE_THRESHOLD_MS=300000  # 5 minutes in milliseconds

if [[ -z "$API_TOKEN" || -z "$NETWORK_ID" ]]; then
  echo "Usage: $0 API_TOKEN NETWORK_ID"
  exit 1
fi

# Fetch network members
response=$(curl -s -H "Authorization: token $API_TOKEN" \
"https://my.zerotier.com/api/v1/network/$NETWORK_ID/member")

if [[ -z "$response" ]]; then
  echo "No response from API"
  exit 2
fi

# Initialize known files if missing
touch "$KNOWN_NODES_FILE" "$KNOWN_ONLINE_FILE"

# Current Unix time in ms
current_ms=$(( $(date +%s) * 1000 ))
threshold=$(( current_ms - ONLINE_THRESHOLD_MS ))

# Extract current nodes array and lastSeen map
mapfile -t current_nodes < <(echo "$response" | jq -r '.[].nodeId // .[].id')
declare -A current_lastSeen=()
while IFS=$'\t' read -r node lastSeen; do
  current_lastSeen["$node"]=$lastSeen
done < <(echo "$response" | jq -r '.[] | "\(.nodeId // .id)\t\(.lastSeen // 0)"')

# Load known nodes and known online nodes
mapfile -t known_nodes < "$KNOWN_NODES_FILE"
mapfile -t known_online_nodes < "$KNOWN_ONLINE_FILE"

# Make associative arrays for lookup
declare -A known_map=()
declare -A known_online_map=()
for n in "${known_nodes[@]}"; do known_map["$n"]=1; done
for n in "${known_online_nodes[@]}"; do known_online_map["$n"]=1; done

# Determine added and removed nodes (presence)
added_nodes=()
removed_nodes=()
for node in "${current_nodes[@]}"; do
  [[ -z ${known_map[$node]} ]] && added_nodes+=("$node")
done
for node in "${known_nodes[@]}"; do
  [[ -z ${current_lastSeen[$node]} ]] && removed_nodes+=("$node")
done

# Notify node join/leave
for node in "${added_nodes[@]}"; do
  node_name=$(echo "$response" | jq -r ".[] | select((.nodeId==\"$node\") or (.id==\"$node\")) | .name // .description // \"(no name)\"")
  notify-send "ZeroTier Alert" "Node joined: $node_name ($node)"
done
for node in "${removed_nodes[@]}"; do
  notify-send "ZeroTier Alert" "Node left: $node"
done

# Determine nodes going online or offline based on lastSeen
new_online_nodes=()
new_offline_nodes=()

for node in "${current_nodes[@]}"; do
  lastSeen=${current_lastSeen[$node]:-0}
  if (( lastSeen > threshold )); then
    # Node considered online now
    if [[ -z ${known_online_map[$node]} ]]; then
      new_online_nodes+=("$node")
    fi
  else
    # Node considered offline now
    if [[ ${known_online_map[$node]} ]]; then
      new_offline_nodes+=("$node")
    fi
  fi
done

# Notify nodes that came online
for node in "${new_online_nodes[@]}"; do
  node_name=$(echo "$response" | jq -r ".[] | select((.nodeId==\"$node\") or (.id==\"$node\")) | .name // .description // \"(no name)\"")
  notify-send "ZeroTier Alert" "Node online: $node_name ($node)"
done

# Notify nodes that went offline
for node in "${new_offline_nodes[@]}"; do
  node_name=$(echo "$response" | jq -r ".[] | select((.nodeId==\"$node\") or (.id==\"$node\")) | .name // .description // \"(no name)\"")
  notify-send "ZeroTier Alert" "Node offline: $node_name ($node)"
done

# Save current node lists
printf "%s\n" "${current_nodes[@]}" > "$KNOWN_NODES_FILE"

# Update online nodes file to current online set
current_online_nodes=()
for node in "${current_nodes[@]}"; do
  lastSeen=${current_lastSeen[$node]:-0}
  if (( lastSeen > threshold )); then
    current_online_nodes+=("$node")
  fi
done
printf "%s\n" "${current_online_nodes[@]}" > "$KNOWN_ONLINE_FILE"