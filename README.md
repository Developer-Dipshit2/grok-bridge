# grok-bridge

CLI bridge from Grok to the on-device **fuckoff** tri stack.

```
Grok CLI /model fuckoff
  -> http://127.0.0.1:18789/v1
  -> A llama.cpp :8080 (Qwen2.5-1.5B)
  -> B Ollama :11434
  -> C CAS sheaf
```

`cloud_tokens=0`. Do not point the CLI at `:8080` or `:11434` directly.

## Install (this tree)

```bash
git clone https://github.com/Developer-Dipshit2/grok-bridge.git
sudo install -m 755 grok-bridge/bin/grok-agi /usr/local/bin/grok-agi
sudo install -m 755 grok-bridge/bin/android-cmd /usr/local/bin/android-cmd
sudo install -m 755 grok-bridge/bin/nexus-md /usr/local/bin/nexus-md
```

Grok CLI overlay (model picker + skills + status line):

```bash
bash grok-bridge/overlay/install.sh
```

`overlay/install.sh` starts `/root/local_grok/start_unified.sh`, which wraps `/root/local_agi_engine/start_engine.sh` only if `:8080` is down.

## Use

```bash
nexus-md status
grok-agi -p '!fast: getprop ro.boot.warranty_bit'
grok-agi -p '!plan: summarize local defense state'
grok-agi -p '!sec: honeyfile trip'
/model fuckoff
```

## Bounds

- Nested TOML `[model.fuckoff]` is read with `.get("model", {}).get("fuckoff", {})`.
- `android-cmd` fallback: getprop → rish → adb → `/system/bin/sh`.
- Never construct `Orchestrator()`. Never cmake llama.cpp on an existing binary.
