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

# Print table in terminal
print_table() {
  printf "%-22s  %-20s  %-20s  %-8s\n" "NODE ID" "NAME/DESCRIPTION" "MANAGED IP(S)" "STATUS"
  printf '%*s\n' 75 '' | tr ' ' '-'
  echo "$response" | jq -c '.[]' | while read -r member; do
    nodeId=$(echo "$member" | jq -r '.nodeId // .id // empty')
    name=$(echo "$member" | jq -r '.name // .description // ""')
    ips=$(echo "$member" | jq -r '.config.ipAssignments // .config.assignedAddresses // [] | join(", ")')
    online=$(echo "$member" | jq -r '.online // false')
    status="Offline"
    [[ "$online" == "true" ]] && status="Online"
    printf "%-22s  %-20s  %-20s  %-8s\n" "$nodeId" "$name" "$ips" "$status"
  done
}

output_html() {
  local file="$1"
  local gen_time
  gen_time=$(date +"%Y-%m-%d %H:%M:%S %Z")

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
</style>
</head>
<body>

<h1>ZeroTier Network Members</h1>
<p id="lastGenerated">Last Generated: $gen_time</p>
<button id="toggleTheme">Switch to Light Mode</button>

<table>
  <thead>
    <tr>
      <th>Node ID</th>
      <th>Name / Description</th>
      <th>Managed IP(s)</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
EOF

  # Append table rows (escaping HTML in name)
  echo "$response" | jq -c '.[]' | while read -r member; do
    nodeId=$(echo "$member" | jq -r '.nodeId // .id // empty')
    name=$(echo "$member" | jq -r '.name // .description // ""' | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
    ips=$(echo "$member" | jq -r '.config.ipAssignments // .config.assignedAddresses // [] | join(", ")')
    online=$(echo "$member" | jq -r '.online // false')
    status="Offline"
    [[ "$online" == "true" ]] && status="Online"
    cat >> "$file" <<ROW
    <tr>
      <td>$nodeId</td>
      <td>$name</td>
      <td>$ips</td>
      <td>$status</td>
    </tr>
ROW
  done

  cat >> "$file" <<'EOF'
  </tbody>
</table>

<script>
  // Helper functions for cookies
  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days*864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/';
  }
  function getCookie(name) {
    return document.cookie.split('; ').reduce((r, v) => {
      const parts = v.split('=');
      return parts[0] === name ? decodeURIComponent(parts[1]) : r
    }, '');
  }

  const toggleBtn = document.getElementById('toggleTheme');
  const body = document.body;

  // Initialize theme from cookie or default dark mode
  const savedTheme = getCookie('theme');
  if (savedTheme === 'light') {
    body.classList.remove('dark-mode');
    toggleBtn.textContent = 'Switch to Dark Mode';
  } else {
    body.classList.add('dark-mode');
    toggleBtn.textContent = 'Switch to Light Mode';
  }

  toggleBtn.addEventListener('click', () => {
    if (body.classList.contains('dark-mode')) {
      body.classList.remove('dark-mode');
      toggleBtn.textContent = 'Switch to Dark Mode';
      setCookie('theme', 'light', 30);
    } else {
      body.classList.add('dark-mode');
      toggleBtn.textContent = 'Switch to Light Mode';
      setCookie('theme', 'dark', 30);
    }
  });
</script>

</body>
</html>
EOF

  echo "HTML report saved to '$file' with Last Generated timestamp: $gen_time"
}


# Run both outputs
print_table
output_html "$HTML_FILE"