#!/bin/bash
# Usage: ./html_ip.sh <api_token> <network_id>
# This script will then output a html file.

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

output_html() {
  local file="$1"
  local gen_time
  gen_time=$(date +"%Y-%m-%d %H:%M:%S %Z")
  local threshold_ms=$(( $(date +%s) * 1000 - 300000 ))  # 5 minutes ago in ms

  cat > "$file" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>ZeroTier Network Members</title>
<style>
  :root {
    --bg-light: #f4f4f4;
    --text-light: #333;
    --table-bg-light: white;
    --table-header-bg-light: #0078D7;
    --table-hover-light: #d1e7fd;
    --title-color-light: black;
    --bg-dark: #121212;
    --text-dark: #ddd;
    --table-bg-dark: #1e1e1e;
    --table-header-bg-dark: #3399ff;
    --table-hover-dark: #264f9c;
    --title-color-dark: #bbb;
  }
  body {
    font-family: Arial, sans-serif;
    margin: 2em;
    background: var(--bg-light);
    color: var(--text-light);
    transition: background-color 0.3s, color 0.3s;
  }
  body.dark-mode {
    background: var(--bg-dark);
    color: var(--text-dark);
  }
  table {
    border-collapse: collapse;
    width: 100%;
    max-width: 900px;
    margin: auto;
    background: var(--table-bg-light);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: background-color 0.3s;
  }
  body.dark-mode table {
    background: var(--table-bg-dark);
    box-shadow: none;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 12px 15px;
    text-align: left;
    vertical-align: middle;
    transition: background-color 0.3s, color 0.3s;
  }
  th {
    background-color: var(--table-header-bg-light);
    color: white;
  }
  body.dark-mode th {
    background-color: var(--table-header-bg-dark);
  }
  tr:nth-child(even) {
    background-color: #f9f9f9;
  }
  body.dark-mode tr:nth-child(even) {
    background-color: #222;
  }
  tr:hover {
    background-color: var(--table-hover-light);
  }
  body.dark-mode tr:hover {
    background-color: var(--table-hover-dark);
  }
  h1 {
    text-align: center;
    margin-bottom: 0.2em;
    color: var(--title-color-light);
    transition: color 0.3s;
  }
  body.dark-mode h1 {
    color: var(--title-color-dark);
  }
  #lastGenerated {
    text-align: center;
    font-style: italic;
    color: gray;
    margin-bottom: 1.5em;
  }
  #toggleTheme {
    display: block;
    margin: 1em auto 2em auto;
    padding: 0.5em 1.2em;
    font-size: 1rem;
    cursor: pointer;
    border: none;
    border-radius: 4px;
    background-color: #0078D7;
    color: white;
    transition: background-color 0.3s;
  }
  #toggleTheme:hover {
    background-color: #005ea1;
  }
  button.copy-btn {
    padding: 3px 8px;
    font-size: 0.85em;
    cursor: pointer;
    background-color: #0078D7;
    border: none;
    border-radius: 3px;
    color: white;
    transition: background-color 0.3s;
  }
  button.copy-btn:hover {
    background-color: #005ea1;
  }
</style>
<script>
function copyToClipboard(ip) {
  navigator.clipboard.writeText(ip).then(() => {
    alert('Copied IP: ' + ip);
  }).catch(() => {
    alert('Copy failed. Please copy manually.');
  });
}
function toggleTheme() {
  document.body.classList.toggle('dark-mode');
}
</script>
</head>
<body class="dark-mode">
<h1>ZeroTier Network Members</h1>
<button id="toggleTheme" onclick="toggleTheme()">Switch to Light/Dark Mode</button>
<p id="lastGenerated">Last Generated: $gen_time</p>
<table>
<thead>
<tr>
  <th>Node ID</th>
  <th>Name / Description</th>
  <th>Managed IP(s)</th>
  <th>Copy IP</th>
  <th>Status</th>
</tr>
</thead>
<tbody>
EOF

  echo "$response" | jq -c --argjson threshold "$threshold_ms" '.[] | {
    nodeId: (.nodeId // .id // ""),
    name: (.name // .description // ""),
    ips: (.config.ipAssignments // .config.assignedAddresses // []),
    lastSeen: .lastSeen
  } | {
    nodeId, name, ips, status: (if (.lastSeen != null and .lastSeen > $threshold) then "Online" else "Offline" end)
  }' | while read -r member; do
    nodeId=$(echo "$member" | jq -r '.nodeId')
    name=$(echo "$member" | jq -r '.name' | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    ips=$(echo "$member" | jq -r '.ips[]?')
    status=$(echo "$member" | jq -r '.status')

    if [[ -z "$ips" ]]; then
      cat >> "$file" <<EOF
<tr>
  <td>$nodeId</td>
  <td>$name</td>
  <td></td>
  <td></td>
  <td>$status</td>
</tr>
EOF
    else
      for ip in $ips; do
        escaped_ip=$(echo "$ip" | sed 's/"/\\"/g')
        cat >> "$file" <<EOF
<tr>
  <td>$nodeId</td>
  <td>$name</td>
  <td>$ip</td>
  <td><button class="copy-btn" onclick="copyToClipboard('$escaped_ip')">Copy</button></td>
  <td>$status</td>
</tr>
EOF
      done
    fi
  done

  cat >> "$file" <<EOF
</tbody>
</table>
</body>
</html>
EOF
}

print_table
output_html "$HTML_FILE"