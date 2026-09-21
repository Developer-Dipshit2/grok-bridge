#!/usr/bin/env bash
# SessionStart: bring up tri daemons if down. Never kill a healthy :8080.
if curl -sf --max-time 1 http://127.0.0.1:8080/health >/dev/null \
   && curl -sf --max-time 1 http://127.0.0.1:18789/health >/dev/null; then
  exit 0
fi
bash /root/local_grok/start_unified.sh >/dev/null 2>&1 || true
exit 0
