#!/usr/bin/env bash
MODEL="$HOME/local_agi_engine/qwen2.5-1.5b-instruct-q4_k_m.gguf"
EXEC="$HOME/local_agi_engine/llama-server"
exec "$EXEC" -m "$MODEL" --host 127.0.0.1 --port 8080 -c 4096 -t $(nproc) --log-disable
