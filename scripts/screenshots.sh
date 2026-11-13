#!/usr/bin/env bash
# Screenshots of the local preview at phone and desktop widths, with headless Chrome.
# Usage: scripts/screenshots.sh OUT_DIR [BASE_URL] [path ...]
# Chrome runs through `systemd-run --user` so that it starts from a clean environment.
set -euo pipefail
out=${1:?output directory}; base=${2:-http://127.0.0.1:8794}; shift 2 || shift $#
paths=("$@"); [ ${#paths[@]} -eq 0 ] && paths=(/ /safha/ /tutorial/02-clean/)
chrome=${CHROME:-/opt/google/chrome/chrome}
mkdir -p "$out"; out=$(cd "$out" && pwd)
prof=$(mktemp -d)
shot() { # name width height url [dark]
  local extra=()
  [ "${5:-}" = dark ] && extra=(--force-dark-mode --blink-settings=preferredColorScheme=0)
  systemd-run --user --wait --collect --quiet --unit="warraq-shot-$RANDOM" "$chrome" --headless=new --disable-gpu \
    --no-first-run --user-data-dir="$prof" --hide-scrollbars --force-device-scale-factor=1 \
    --window-size="$2,$3" --virtual-time-budget=4000 "${extra[@]}" --screenshot="$out/$1.png" "$4" >/dev/null 2>&1
}
for p in "${paths[@]}"; do
  name=$(echo "$p" | sed 's#^/##; s#/$##; s#/#-#g'); name=${name:-home}
  shot "$name-phone" 390 1500 "$base$p"
  shot "$name-desktop" 1366 1100 "$base$p"
done
shot "home-phone-dark" 390 1500 "$base/" dark
rm -rf "$prof"
ls -1 "$out"
