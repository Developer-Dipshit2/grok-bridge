#!/usr/bin/env python3
"""Honeyfile watcher. One POST to :18789 on trip. Does not poll models."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, "/root/local_grok")
from agi_bridge import canary_append, patch_snapshot  # noqa: E402

HONEY = ["/data/local/tmp/su", "/data/local/tmp/id"]
PID = Path("/root/local_grok/state/honey_watch.pid")
ENGINE = "http://127.0.0.1:18789/run"
ANDROID_CMD = "/usr/local/bin/android-cmd"
INTERVAL = 2.0


def _stat(path: str) -> str:
    if os.path.exists(ANDROID_CMD):
        try:
            r = subprocess.run(
                [ANDROID_CMD, f"stat -c %Y-%s {path} 2>/dev/null || echo missing"],
                capture_output=True, text=True, timeout=5,
            )
            return (r.stdout or "").strip() or "missing"
        except Exception as e:
            return f"err:{e}"
    try:
        st = os.stat(path)
        return f"{int(st.st_mtime)}-{st.st_size}"
    except OSError:
        return "missing"


def _fire(path: str) -> None:
    canary_append(f"HONEYFILE trip {path}")
    try:
        patch_snapshot(1.0, "HALT", traps=1)
    except Exception:
        pass
    payload = json.dumps({"mode": "agi", "directive": f"AGI sec honeyfile {path}"}).encode()
    req = urllib.request.Request(ENGINE, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=180).read()
    except Exception:
        pass


def main() -> None:
    PID.parent.mkdir(parents=True, exist_ok=True)
    PID.write_text(str(os.getpid()), encoding="utf-8")
    last = {p: _stat(p) for p in HONEY}
    while True:
        time.sleep(INTERVAL)
        for p in HONEY:
            now = _stat(p)
            if now != last[p]:
                last[p] = now
                if now != "missing":
                    _fire(p)
        # idle curiosity: one queued topic, only if :8080 is up
        try:
            if int(time.time()) % 30 < INTERVAL:
                import urllib.request
                urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1)
                sys.path.insert(0, "/root/nexus_system")
                from nexus_curiosity_engine import process_queue
                process_queue()
        except Exception:
            pass


if __name__ == "__main__":
    main()
