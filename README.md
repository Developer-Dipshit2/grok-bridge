# grok-bridge

CLI bridge from Grok-style commands (`grok-agi`, `-p`, `--think`) to your local or remote AGI over an OpenAI-compatible `/v1/chat/completions` endpoint.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Developer-Dipshit2/grok-bridge/main/install-grok-agi.sh | bash
```

Or clone and run:

```bash
git clone https://github.com/Developer-Dipshit2/grok-bridge.git
bash grok-bridge/install-grok-agi.sh
```

Non-interactive:

```bash
AGI_BASE_URL='http://127.0.0.1:11434/v1' \
AGI_MODEL='llama3' \
AGI_API_KEY='' \
bash install-grok-agi.sh
```

## Use

```bash
export PATH="$HOME/.grok/bin:$PATH"
grok-agi
grok-agi -p "Say hello from my AGI"
grok-agi --think -p "Design a plan"
```

Config is written to `~/.grok/config.env`.
Requires `bash`, `python3`, and a reachable AGI base URL.
