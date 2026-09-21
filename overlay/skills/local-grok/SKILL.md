---
name: local-grok
description: Dispatch work to on-device fuckoff tri stack (A:8080 B:11434 C:CAS). Use for local processing, zero cloud tokens, /local-grok, /lgrok, /fuckoff, or process this locally.
user-invocable: true
---

# fuckoff tri

Do not solve the task in the cloud session. Hand it to the on-device tri multiplexer.

1. If `curl -sf --max-time 1 http://127.0.0.1:18789/health` fails, run `bash /root/local_grok/start_unified.sh`. Do not kill llama-server on :8080 if it is already healthy.
2. Run exactly one job:

```bash
python3 /usr/local/bin/grok-agi -p "<user directive, verbatim>"
```

3. Return that stdout unchanged, plus `cloud_tokens=0 (fuckoff tri 1.5B)`.
4. Never construct Orchestrator(). Never cmake llama.cpp. Never call api.x.ai.
