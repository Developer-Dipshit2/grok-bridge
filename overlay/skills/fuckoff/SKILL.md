---
name: fuckoff
description: Run a prompt on the on-device fuckoff tri model (llama.cpp:8080 + Ollama + CAS sheaf). /fuckoff
user-invocable: true
---

Ensure `bash /root/local_grok/start_unified.sh` only if :18789 health fails. Then:

```bash
python3 /usr/local/bin/grok-agi -p "<arguments after /fuckoff>"
```

Return stdout only. `cloud_tokens=0`. No Orchestrator(). No cmake.
