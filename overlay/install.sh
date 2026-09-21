#!/usr/bin/env bash
# Overlay-only install. No cmake, no ollama pull if tagged, no deploy.py.
# Integration:
#  1. start_unified.sh = tri (18789 + honey). It calls start_engine.sh only if :8080 is down.
#  2. grok-agi reads env → ~/.grok/config.env → config.toml [model.fuckoff].base_url.
#  3. android-cmd keeps getprop / rish / adb / /system/bin/sh fallbacks.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "[*] nexus-md 0.1.0-beta overlay from $ROOT"
install -m 755 "$ROOT/bin/nexus-md" /usr/local/bin/nexus-md
install -m 755 "$ROOT/bin/grok-agi" /usr/local/bin/grok-agi
install -m 755 "$ROOT/bin/android-cmd" /usr/local/bin/android-cmd
mkdir -p /root/.grok/skills /root/.grok/hooks /root/.grok/state
cp -a "$ROOT/grok-overlay/skills/." /root/.grok/skills/
cp -a "$ROOT/grok-overlay/hooks/." /root/.grok/hooks/
install -m 755 "$ROOT/grok-overlay/statusline.sh" /root/.grok/statusline.sh
if [ -f "$ROOT/grok-overlay/config.env" ]; then
  cp -a "$ROOT/grok-overlay/config.env" /root/.grok/config.env
fi
# append model block only if missing — never wipe existing toml
if ! grep -q '^\[model.fuckoff\]' /root/.grok/config.toml 2>/dev/null; then
  cat "$ROOT/grok-overlay/config.fragment.toml" >> /root/.grok/config.toml
fi
UNIFIED=/root/local_grok/start_unified.sh
LLAMA_LAUNCH=/root/local_agi_engine/start_engine.sh
if [ ! -x "$UNIFIED" ] || [ ! -x "$LLAMA_LAUNCH" ]; then
  echo "[!] missing $UNIFIED or $LLAMA_LAUNCH" >&2
  exit 1
fi
grep -q start_engine.sh "$UNIFIED" || { echo "[!] $UNIFIED does not wrap start_engine.sh" >&2; exit 1; }
bash "$UNIFIED"
echo "[+] overlay installed. New Grok sessions: /model fuckoff"
echo "    This open TUI must restart to pick up status line."
