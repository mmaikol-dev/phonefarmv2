#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="/home/atlas/PHONE FARM"
SCRCPY_DIR="$ROOT_DIR/tools/scrcpy-v3.3.4"
SCRCPY_BIN="$SCRCPY_DIR/scrcpy"
ADB_BIN="${ADB:-/usr/bin/adb}"
DEVICE_SERIAL="${ANDROID_SERIAL:-aece3bbd}"
AUDIO_SOURCE="${SCRCPY_AUDIO_SOURCE:-output}"
USER_ID="$(id -u)"
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$USER_ID}"

if [[ ! -x "$SCRCPY_BIN" ]]; then
  echo "scrcpy binary not found at: $SCRCPY_BIN" >&2
  exit 1
fi

if [[ ! -x "$ADB_BIN" ]]; then
  echo "adb binary not found at: $ADB_BIN" >&2
  exit 1
fi

echo "Starting phone audio"
echo "  device: $DEVICE_SERIAL"
echo "  audio source: $AUDIO_SOURCE"
echo "  adb: $ADB_BIN"
echo "  xdg runtime dir: $XDG_RUNTIME_DIR"

export ADB="$ADB_BIN"
export ANDROID_SERIAL="$DEVICE_SERIAL"
export XDG_RUNTIME_DIR

if [[ -z "${SDL_AUDIODRIVER:-}" ]]; then
  if command -v pactl >/dev/null 2>&1; then
    export SDL_AUDIODRIVER="pulseaudio"
  fi
fi

if [[ -n "${SDL_AUDIODRIVER:-}" ]]; then
  echo "  sdl audio driver: $SDL_AUDIODRIVER"
fi

exec "$SCRCPY_BIN" \
  --no-video \
  --no-window \
  --require-audio \
  --audio-source="$AUDIO_SOURCE" \
  "$@"
