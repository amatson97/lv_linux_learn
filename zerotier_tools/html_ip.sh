#!/bin/bash
# ZeroTier Network HTML Report Generator
# Description: Generates an HTML page showing all ZeroTier network members with IPs and status
#
# Usage: ./html_ip.sh [API_TOKEN] [NETWORK_ID] [output_file]
#   If tokens not provided as arguments, you'll be prompted interactively
#   Or set environment variables: ZEROTIER_API_TOKEN and ZEROTIER_NETWORK_ID
#   Output file defaults to: zerotier_members.html

set -euo pipefail

# Includes
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
# shellcheck source=/dev/null
source "$repo_root/includes/main.sh"

HTML_FILE="${3:-zerotier_members.html}"

# Get credentials (from args, env vars, or prompts)
if [ -n "${1:-}" ]; then
  API_TOKEN="$1"
else
  API_TOKEN=$(prompt_zerotier_token) || exit 1
fi

if [ -n "${2:-}" ]; then
  NETWORK_ID="$2"
else
  NETWORK_ID=$(prompt_zerotier_network) || exit 1
fi

green_echo "[*] Generating HTML report for network: $NETWORK_ID"

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
<script>
(() => {
  const CHECK_INTERVAL = 30000;
  let lastModified = document.lastModified;

  function checkForUpdate() {
    fetch(window.location.href, { method: 'HEAD', cache: 'no-store' })
      .then(response => {
        const newModified = response.headers.get('Last-Modified');
        if (newModified && newModified !== lastModified) {
          window.location.reload(true);
        }
      })
      .catch(console.error);
  }

  setInterval(checkForUpdate, CHECK_INTERVAL);
})();
</script>

</body>
</html>
EOF
}

print_table
output_html "$HTML_FILE"