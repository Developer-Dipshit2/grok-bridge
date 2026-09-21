#!/usr/bin/env bash
# one entry: llama.cpp :8080 + local-grok tools :18789
set -e
if ! curl -sf --max-time 1 http://127.0.0.1:8080/health >/dev/null; then
  nohup bash /root/local_agi_engine/start_engine.sh \
    >>/root/local_agi_engine/engine.log 2>&1 &
  echo $! >/root/local_agi_engine/llama-server.pid
fi
if ! curl -sf --max-time 1 http://127.0.0.1:18789/health >/dev/null; then
  nohup python3 /root/local_grok/engine.py serve >>/root/local_grok/logs/daemon.log 2>&1 &
  echo $! >/root/local_grok/local_grok.pid
fi
HWPIDF=/root/local_grok/state/honey_watch.pid
if [ -f "$HWPIDF" ] && kill -0 "$(cat "$HWPIDF")" 2>/dev/null; then
  :
else
  mkdir -p /root/local_grok/state /root/local_grok/logs
  nohup python3 /root/local_grok/honey_watch.py >>/root/local_grok/logs/honey_watch.log 2>&1 &
  echo $! >"$HWPIDF"
fi
for i in $(seq 1 20); do
  curl -sf --max-time 1 http://127.0.0.1:8080/health >/dev/null && \
  curl -sf --max-time 1 http://127.0.0.1:18789/health >/dev/null && break
  sleep 0.5
done
echo -n '8080 '; curl -s --max-time 1 http://127.0.0.1:8080/health; echo
echo -n '18789 '; curl -s --max-time 1 http://127.0.0.1:18789/health; echo
