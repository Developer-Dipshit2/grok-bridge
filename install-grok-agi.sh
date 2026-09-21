#!/usr/bin/env bash
set -eo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}========================================================================${NC}"
echo -e "${BOLD}       INSTALLING GROK-AGI RUNTIME INTERFACE (LOCAL / REMOTE)           ${NC}"
echo -e "${CYAN}========================================================================${NC}\n"

if [ -z "$AGI_BASE_URL" ]; then
    if [ -t 0 ] || [ -c /dev/tty ]; then
        read -r -p "Enter Base URL [default: http://127.0.0.1:11434/v1]: " INPUT_URL </dev/tty || true
        AGI_BASE_URL="${INPUT_URL:-http://127.0.0.1:11434/v1}"
    else
        AGI_BASE_URL="http://127.0.0.1:11434/v1"
    fi
fi

if [ -z "$AGI_MODEL" ]; then
    if [ -t 0 ] || [ -c /dev/tty ]; then
        read -r -p "Enter Model ID (e.g., llama3, mistral, qwen): " INPUT_MODEL </dev/tty || true
        AGI_MODEL="$INPUT_MODEL"
    fi
fi

if [ -z "$AGI_MODEL" ]; then
    echo -e "${RED}[!] Error: Model ID is required.${NC}"
    echo "    AGI_MODEL=llama3 bash $0"
    exit 1
fi

if [ -z "$AGI_API_KEY" ]; then
    if [ -t 0 ] || [ -c /dev/tty ]; then
        read -r -p "Enter API Key [press Enter if none]: " INPUT_KEY </dev/tty || true
        AGI_API_KEY="$INPUT_KEY"
    fi
fi

INSTALL_DIR="$HOME/.grok/bin"
CONFIG_DIR="$HOME/.grok"
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR"

cat << CONFIG_EOF > "$CONFIG_DIR/config.env"
AGI_BASE_URL="${AGI_BASE_URL}"
AGI_MODEL="${AGI_MODEL}"
AGI_API_KEY="${AGI_API_KEY}"
CONFIG_EOF
chmod 600 "$CONFIG_DIR/config.env"

cat << 'BIN_EOF' > "$INSTALL_DIR/grok-agi"
#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

CONFIG_PATH = os.path.expanduser("~/.grok/config.env")

config = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k] = v.strip('"').strip("'")

base_url = os.environ.get("AGI_BASE_URL", config.get("AGI_BASE_URL", "http://127.0.0.1:11434/v1"))
model = os.environ.get("AGI_MODEL", config.get("AGI_MODEL", ""))
api_key = os.environ.get("AGI_API_KEY", config.get("AGI_API_KEY", ""))

if not model:
    print("\033[0;31m[!] Model ID is not configured. Edit ~/.grok/config.env or set AGI_MODEL.\033[0m", file=sys.stderr)
    sys.exit(1)

endpoint = f"{base_url.rstrip('/')}/chat/completions"

THINK_SYSTEM = (
    "Think step by step before answering. Put private reasoning in "
    "<think>...</think>, then give the final answer after it."
)


def parse_args(argv):
    think = False
    prompt_parts = []
    for a in argv:
        if a in ("-h", "--help"):
            print("Usage: grok-agi [--think] [-p] [prompt...]")
            print("  grok-agi")
            print("  grok-agi -p \"Say hello\"")
            print("  grok-agi --think -p \"Design a plan\"")
            sys.exit(0)
        if a == "--think":
            think = True
        elif a != "-p":
            prompt_parts.append(a)
    return think, " ".join(prompt_parts).strip()


def stream_chat(prompt, think=False):
    messages = []
    if think:
        messages.append({"role": "system", "content": THINK_SYSTEM})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "stream": True}
    if think:
        payload["reasoning_effort"] = "high"
    headers = {"Content-Type": "application/json", "User-Agent": "grok-agi/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    def post(body):
        req = urllib.request.Request(
            endpoint, data=json.dumps(body).encode("utf-8"), headers=headers
        )
        return urllib.request.urlopen(req)

    try:
        with post(payload) as resp:
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content") or delta.get("reasoning_content") or ""
                    sys.stdout.write(token)
                    sys.stdout.flush()
                except Exception:
                    pass
        print()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        fallback = dict(payload)
        fallback.pop("stream", None)
        fallback.pop("reasoning_effort", None)
        try:
            with post(fallback) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                msg = body.get("choices", [{}])[0].get("message", {})
                print(msg.get("content") or msg.get("reasoning_content") or json.dumps(body))
                return
        except Exception:
            print(f"\n\033[0;31m[!] HTTP Error {e.code}: {err}\033[0m", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"\n\033[0;31m[!] Connection Error: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


def interactive(think=False):
    mode = "think" if think else "chat"
    print(f"\033[0;36m=== Grok-AGI [{model}] ({mode}) — type exit to quit ===\033[0m")
    while True:
        try:
            prompt = input("\033[1mgrok>\033[0m ").strip()
            if not prompt:
                continue
            if prompt in ("exit", "quit"):
                break
            stream_chat(prompt, think=think)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    think, prompt = parse_args(sys.argv[1:])
    if prompt:
        stream_chat(prompt, think=think)
    else:
        interactive(think=think)
BIN_EOF

chmod 755 "$INSTALL_DIR/grok-agi"

SHELL_RC="$HOME/.bashrc"
if ! grep -q '\.grok/bin' "$SHELL_RC" 2>/dev/null; then
    printf '\nexport PATH="$HOME/.grok/bin:$PATH"\n' >> "$SHELL_RC"
fi

echo -e "${GREEN}${BOLD}[+] Installation Complete!${NC}"
echo -e "  - Config File : ~/.grok/config.env"
echo -e "  - Binary Path : ~/.grok/bin/grok-agi"
echo -e "  - Model       : ${AGI_MODEL}"
echo -e "  - Base URL    : ${AGI_BASE_URL}"
echo
echo "  export PATH=\"\$HOME/.grok/bin:\$PATH\""
echo "  grok-agi"
echo "  grok-agi -p \"Say hello from my AGI\""
echo "  grok-agi --think -p \"Design a plan\""
