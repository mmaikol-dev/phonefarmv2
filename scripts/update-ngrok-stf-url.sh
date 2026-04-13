#!/usr/bin/env bash
# Update the STF ngrok URL in the Docker container and .env when ngrok restarts.
# Usage: ./scripts/update-ngrok-stf-url.sh [new-stf-ngrok-url]
# Example: ./scripts/update-ngrok-stf-url.sh https://abc123.ngrok-free.app
#
# If no argument is given, fetches the current URL from the ngrok API.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -ge 1 ]]; then
    STF_URL="${1%/}"
else
    STF_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin).get('tunnels', [])
for t in tunnels:
    if t.get('name') == 'stf':
        print(t['public_url'].rstrip('/'))
        break
" 2>/dev/null || true)
fi

if [[ -z "$STF_URL" ]]; then
    echo "ERROR: Could not determine STF ngrok URL. Pass it as an argument or start ngrok first."
    exit 1
fi

echo "Updating STF public URL to: $STF_URL"

# 1. Update .env
if grep -q "^STF_PUBLIC_BASE_URL=" .env; then
    sed -i "s|^STF_PUBLIC_BASE_URL=.*|STF_PUBLIC_BASE_URL=${STF_URL}|" .env
else
    echo "STF_PUBLIC_BASE_URL=${STF_URL}" >> .env
fi

# 2. Update screen-ws-url-pattern in the container
docker exec phonefarm-stf sed -i \
    "s|default: 'wss://[^']*'|default: 'wss://${STF_URL#https://}/screen-ws'|" \
    /app/lib/cli/local/index.js

# 3. Update websocket URL in the container
docker exec phonefarm-stf sed -i \
    "s||| https://[^/']*\\.ngrok-free\\.app/'||| ${STF_URL}/'|" \
    /app/lib/cli/local/index.js || true
# Simpler approach: replace directly
docker exec phonefarm-stf node -e "
const fs = require('fs');
let c = fs.readFileSync('/app/lib/cli/local/index.js', 'utf8');
c = c.replace(/argv\.websocketUrl \|\| 'https:\/\/[^']*'/, \"argv.websocketUrl || '${STF_URL}/'\");
fs.writeFileSync('/app/lib/cli/local/index.js', c);
"

# 4. Restart STF to apply changes
echo "Restarting STF container..."
docker restart phonefarm-stf

echo "Done. STF URL updated to ${STF_URL}"
echo "Laravel config cleared to pick up new .env..."
php artisan config:clear 2>/dev/null || true
