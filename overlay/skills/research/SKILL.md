---
name: research
description: On-device curiosity engine (DDG+Wiki distilled on :8080, vault at learned_memory.json). /research /learn
user-invocable: true
---

```bash
python3 /root/nexus_system/nexus_curiosity_engine.py "<topic>"
```

Cache hits skip the network. Distill uses :8080 only, never cloud.
