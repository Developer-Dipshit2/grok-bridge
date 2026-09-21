#!/usr/bin/env bash
# Grok status row: model + tri health. Curl only on refresh_interval.
CACHE=/root/.grok/state/tri_health.cache
mkdir -p /root/.grok/state
input=$(cat)
model=$(printf '%s' "$input" | python3 -c 'import json,sys
d=json.load(sys.stdin)
print(((d.get("model") or {}).get("display_name")) or ((d.get("model") or {}).get("id")) or "?")' 2>/dev/null)
trigger=$(printf '%s' "$input" | python3 -c 'import json,sys
d=json.load(sys.stdin)
print(d.get("trigger") or "state")' 2>/dev/null)
if [ "$trigger" = "refresh_interval" ] || [ ! -f "$CACHE" ]; then
  a=down; b=down; tri=no
  curl -sf --max-time 1 http://127.0.0.1:8080/health >/dev/null && a=ok
  h=$(curl -sf --max-time 1 http://127.0.0.1:18789/health 2>/dev/null || true)
  [ -n "$h" ] && b=ok
  printf '%s' "$h" | grep -q '"tri": true' && tri=tri
  echo "$a $b $tri" >"$CACHE"
else
  read -r a b tri <"$CACHE" || { a=?; b=?; tri=?; }
fi
printf 'fuckoff-cli │ %s │ 8080=%s 18789=%s %s │ cloud=0\n' "${model:-?}" "$a" "$b" "$tri"
