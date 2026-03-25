#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"

echo "Choose automation:"
echo "1. Spotify"
echo "2. Spotify Moondream"
echo "3. Instagram Auto"
echo "4. Instagram Liker"
printf "> "
read -r choice

case "$choice" in
  1)
    exec python3 automation/spotify_auto.py
    ;;
  2)
    exec python3 automation/spotify_moondream.py
    ;;
  3)
    exec python3 automation/instagram_auto.py
    ;;
  4)
    exec python3 automation/instagram_liker.py
    ;;
  *)
    echo "Invalid choice."
    exit 1
    ;;
esac
