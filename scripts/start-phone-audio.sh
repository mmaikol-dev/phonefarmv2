#!/usr/bin/env bash
# Start the phone audio HTTP stream server.
#
# PhoneAudioService calls this via:
#   ANDROID_SERIAL=<s> SCRCPY_AUDIO_SOURCE=<src> nohup ./scripts/start-phone-audio.sh > ... &
#
# The script exec's into Node so the PID tracked by PhoneAudioService IS the
# Node process. Killing it sends SIGTERM, which the Node script catches and
# forwards to scrcpy before exiting.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_SCRIPT="$ROOT_DIR/scripts/audio-stream-server.cjs"

# Resolve Node binary — prefer NVM's node 24+ if available, then fall back to
# whatever is on PATH (or the NODE env var override).
if [[ -z "${NODE:-}" ]]; then
    NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
    if [[ -s "$NVM_DIR/nvm.sh" ]]; then
        # Source nvm silently and use node 24 if installed
        # shellcheck disable=SC1091
        source "$NVM_DIR/nvm.sh" --no-use 2>/dev/null || true
        NVM24="$(nvm which 24 2>/dev/null || true)"
        if [[ -x "$NVM24" ]]; then
            NODE_BIN="$NVM24"
        else
            NODE_BIN="node"
        fi
    else
        NODE_BIN="node"
    fi
else
    NODE_BIN="$NODE"
fi

if [[ ! -f "$SERVER_SCRIPT" ]]; then
    echo "ERROR: audio-stream-server.cjs not found at $SERVER_SCRIPT" >&2
    exit 1
fi

SCRCPY_BIN="$ROOT_DIR/tools/scrcpy-v3.3.4/scrcpy"
if [[ ! -x "$SCRCPY_BIN" ]]; then
    echo "ERROR: scrcpy not found at $SCRCPY_BIN" >&2
    exit 1
fi

export ANDROID_SERIAL="${ANDROID_SERIAL:-}"
export SCRCPY_AUDIO_SOURCE="${SCRCPY_AUDIO_SOURCE:-output}"
export AUDIO_PORT="${AUDIO_PORT:-7201}"

echo "Starting phone audio stream server"
echo "  device:  ${ANDROID_SERIAL:-any}"
echo "  source:  $SCRCPY_AUDIO_SOURCE"
echo "  port:    $AUDIO_PORT"

exec "$NODE_BIN" "$SERVER_SCRIPT"
