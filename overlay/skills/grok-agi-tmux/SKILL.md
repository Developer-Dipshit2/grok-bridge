---
name: grok-agi-tmux
description: Launch grok-agi Quad HUD in tmux (llama :8080, Ollama, CAS, Amara). Use when the user says grok-agi-tmux, /grok-agi-tmux, or wants the 4-pane telemetry panel.
user-invocable: true
---

```bash
bash /root/nexus_system/grok_agi_tmux.sh
```

If already in a tool session, start detached then confirm:

```bash
bash /root/local_grok/start_unified.sh
bash /root/nexus_system/start_quad_tmux.sh
tmux ls
```

User attaches with `tmux attach -t quad`.
