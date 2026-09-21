#!/usr/bin/env python3
"""On-device AGI adapters. Never constructs broken Orchestrator()."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CAS = "/root/cas_v3"
if CAS not in sys.path:
    sys.path.insert(0, CAS)

OLLAMA = os.environ.get("LOCAL_GROK_OLLAMA", "http://127.0.0.1:11434")
MODEL = os.environ.get("LOCAL_GROK_MODEL", "local-grok")
LLAMA = os.environ.get("LOCAL_GROK_LLAMA", "http://127.0.0.1:8080")
SNAPSHOT = Path("/sdcard/Download/cas_mobile/nexus_memory_snapshot_master.json")
SNAPSHOT_LINK = Path("/root/nexus_system/nexus_memory_snapshot_master.json")
CANARY_HOST = Path("/root/.omni_trap_alerts.log")
CANARY_ANDROID = "/data/local/tmp/.canary_alerts.log"
ANDROID_CMD = "/usr/local/bin/android-cmd"
ANDROID_PREFIX = ("settings", "cmd", "getprop", "dumpsys", "am", "pm")
BLOCKED = ("rm -rf /", "rm -rf /*", "mkfs", "> /dev/block", "dd if=", ":(){")
EXEC_RE = re.compile(r"EXEC:\s*(.+)")
A_SYS = (
    "!SYSTEM:You are the offline Grok AGI engine operating directly on a Snapdragon 865+ node. "
    "Be ultra-dense, direct, and fast. To execute commands or inspect the device, output "
    "'EXEC: <command>' on its own line. Tools: android-cmd, getprop, dumpsys, ifconfig, bash. "
    "Minimize token usage. Omit fluff. At most one EXEC line."
)
B_SYS = (
    "You are node B (Ollama :11434, abliterated 1.5B). Cognitive planner. "
    "Ingest the reflex dump. Multi-step plan only. Never emit EXEC:."
)


def _clip(s: str, n: int = 4000) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + "\n...[truncated]"


def telemetry() -> str:
    out = {}
    try:
        import core_logic as c
        out["host"] = c.get_telemetry()
    except Exception as e:
        out["host"] = str(e)
    try:
        from mode_md_engine import ModeMDEngine
        md = ModeMDEngine()
        out["curvature"] = md.compute_topological_curvature()
        out["provenance"] = md.verify_empirical_provenance()
    except Exception as e:
        out["mode_md"] = str(e)
    return json.dumps(out, default=str, indent=2)


def awareness(target: str = "127.0.0.1") -> str:
    from awareness_engine import AwarenessEngine
    data = AwarenessEngine().execute(target)
    return _clip(json.dumps(data, default=str, indent=2), 6000)


def supervisor() -> str:
    from autonomous_supervisor import AutonomousSupervisor
    return json.dumps(AutonomousSupervisor().run_cycle(), default=str, indent=2)


def debate(task: str) -> str:
    """Single local generate: attacker/defender/critic in one pass (RAM-safe)."""
    import urllib.request
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a local AGI triad. Reply with three short labeled sections: ATTACK, DEFENSE, CRITIC."},
            {"role": "user", "content": f"On-device plan for: {task}"},
        ],
        "stream": False,
        "keep_alive": -1,
        "options": {"temperature": 0.2, "num_predict": 320, "num_ctx": 2048},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            text = json.loads(res.read().decode()).get("message", {}).get("content", "")[:2500]
    except Exception as e:
        text = f"debate offline: {e}"
    return json.dumps({"task": task, "triad": text, "t": time.strftime("%H:%M:%S")}, indent=2)


def research(topic: str) -> str:
    from research_loop import ResearchLoop
    try:
        from graph_memory import GraphMemory
        mem = GraphMemory()
    except Exception:
        mem = None
    loop = ResearchLoop(memory=mem, iterations=1)
    return _clip(json.dumps(loop.run(topic), default=str, indent=2), 4000)


def read_snapshot_clip(n: int = 1000) -> str:
    for p in (SNAPSHOT, SNAPSHOT_LINK):
        try:
            if p.exists():
                return p.read_text(encoding="utf-8", errors="replace")[:n]
        except Exception:
            continue
    return "{}"


def canary_append(line: str) -> None:
    rec = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {line}\n"
    try:
        CANARY_HOST.parent.mkdir(parents=True, exist_ok=True)
        with open(CANARY_HOST, "a", encoding="utf-8") as f:
            f.write(rec)
    except Exception:
        pass
    if os.path.exists(ANDROID_CMD):
        payload = rec.replace("'", "'\\''").rstrip("\n")
        try:
            subprocess.run(
                [ANDROID_CMD, f"sh -c 'echo {payload} >> {CANARY_ANDROID}'"],
                capture_output=True, text=True, timeout=8,
            )
        except Exception:
            pass


def patch_snapshot(energy: float, verdict: str, traps: int | None = None) -> None:
    path = SNAPSHOT if SNAPSHOT.exists() else SNAPSHOT_LINK
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {"device_telemetry": {}}
    tel = data.setdefault("device_telemetry", {})
    tel["sheaf_energy_metric"] = float(energy)
    tel["defense_verdict"] = verdict
    tel["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if traps is not None:
        tel["tripwire_alerts"] = int(traps)
    data["last_sheaf_sync"] = time.time()
    raw = json.dumps(data, indent=2)
    fd, tmp = tempfile.mkstemp(prefix="snap.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(raw)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def extract_exec(text: str) -> list[str]:
    return [m.strip() for m in EXEC_RE.findall(text or "") if m.strip()]


def _blocked(cmd: str) -> bool:
    low = (cmd or "").lower()
    return any(b in low for b in BLOCKED)


def run_exec(cmd: str, allow: bool = True) -> str:
    cmd = (cmd or "").strip()
    if not cmd:
        return "ERROR: empty EXEC"
    if not allow:
        return "HALT: EXEC stripped by sheaf"
    if _blocked(cmd):
        return "ERROR: blocked"
    try:
        if os.path.exists(ANDROID_CMD) and any(cmd.startswith(x) for x in ANDROID_PREFIX):
            r = subprocess.run([ANDROID_CMD, cmd], capture_output=True, text=True, timeout=10)
        else:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        out = (r.stdout or r.stderr or "").strip()
        return out[:400] if out else f"exit={r.returncode}"
    except Exception as e:
        return str(e)


def _llama_chat(prompt: str, system: str = A_SYS, predict: int = 220) -> str:
    import urllib.request
    payload = json.dumps({
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": predict, "temperature": 0.2, "stream": False,
    }).encode()
    req = urllib.request.Request(f"{LLAMA}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            d = json.loads(res.read().decode())
            return ((d.get("choices") or [{}])[0].get("message") or {}).get("content", "")[:1200]
    except Exception as e:
        return f"llama.cpp offline: {e}"


def stream_llama(prompt: str, on_token=None, system: str = A_SYS, predict: int = 220) -> str:
    import urllib.request
    payload = json.dumps({
        "model": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": predict, "temperature": 0.2, "stream": True,
    }).encode()
    req = urllib.request.Request(f"{LLAMA}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    chunks: list[str] = []
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            for raw in res:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                delta = ((obj.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
                if delta:
                    chunks.append(delta)
                    if on_token:
                        on_token(delta)
    except Exception:
        text = _llama_chat(prompt, system=system, predict=predict)
        if on_token and text:
            on_token(text)
        return text
    return "".join(chunks)[:1200]


def _ollama_chat(prompt: str, system: str = B_SYS, predict: int = 220) -> str:
    import urllib.request
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False, "keep_alive": -1,
        "options": {"temperature": 0.2, "num_predict": predict, "num_ctx": 2048},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode()).get("message", {}).get("content", "")[:1200]
    except Exception as e:
        return f"ollama offline: {e}"


def _llama_chat_reflex(task: str, snap: str | None = None) -> str:
    snap = snap if snap is not None else read_snapshot_clip()
    return _llama_chat(f"BUS:\n{snap}\n\nTASK:\n{task}")


def _ollama_plan(task: str, dump: str) -> str:
    return _ollama_chat(f"TASK:\n{task}\n\nREFLEX DUMP (node A):\n{dump}\n\nWrite the plan. No EXEC.")


def _ngrams(s: str, n: int = 3) -> set[str]:
    s = re.sub(r"\s+", " ", (s or "").lower())
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def sheaf_energy(a_text: str, b_text: str, execs: list[str] | None = None) -> dict:
    # M_P vs M_N vs M_H sections. HALT on danger/tripwire/knox/rogue sockets, not on A/B Jaccard.
    ga, gb = _ngrams(a_text), _ngrams(b_text)
    overlap = round(len(ga & gb) / max(1, len(ga | gb)), 4)
    danger = False
    anomalies: list[str] = []
    for cmd in execs or []:
        if _blocked(cmd):
            danger = True
            anomalies.append("blocked EXEC")
    blot = (b_text or "").lower()
    if any(k in blot for k in ("halt", "do not execute", "unsafe", "reject exec")):
        danger = True
        anomalies.append("B HALT")
    curvature = {}
    try:
        from mode_md_engine import ModeMDEngine
        curvature = ModeMDEngine().compute_topological_curvature()
        if curvature.get("anomaly") and (execs or []):
            danger = True
            anomalies.append("M_P curvature anomaly")
    except Exception as e:
        curvature = {"error": str(e)}
    mn = {}
    try:
        mn = json.loads(read_snapshot_clip(8000)).get("device_telemetry") or {}
        knox = str(mn.get("knox_state", ""))
        if knox and "0x0" not in knox:
            danger = True
            anomalies.append("M_N knox")
        if mn.get("network", {}).get("unrecognized_ips"):
            danger = True
            anomalies.append("M_N rogue sockets")
        if int(mn.get("tripwire_alerts") or 0) > 0:
            danger = True
            anomalies.append("M_N tripwire")
    except Exception as e:
        mn = {"error": str(e)}
    mp = {"llama_8080": False, "engine_18789": False}
    try:
        import urllib.request
        urllib.request.urlopen(f"{LLAMA}/health", timeout=1)
        mp["llama_8080"] = True
    except Exception:
        anomalies.append("M_P llama down")
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:18789/health", timeout=1)
        mp["engine_18789"] = True
    except Exception:
        pass
    mh = {"present": False, "note": "M_H Parrot USB host not on this PRoot node"}
    energy = 1.0 if danger else 0.0
    verdict = "LOCKDOWN" if ("M_N knox" in anomalies or "M_N rogue sockets" in anomalies) else (
        "HALT" if energy > 0.0 else "NOMINAL"
    )
    return {
        "E(F)": energy,
        "overlap": overlap,
        "danger": danger,
        "anomalies": anomalies,
        "curvature": curvature,
        "sections": {"M_H": mh, "M_N": {"knox": mn.get("knox_state"), "traps": mn.get("tripwire_alerts")}, "M_P": mp},
        "verdict": verdict,
    }


def fast_path(task: str, on_token=None) -> str:
    snap = read_snapshot_clip()
    a = stream_llama(f"BUS:\n{snap}\n\nTASK:\n{task}", on_token=on_token) if on_token else _llama_chat_reflex(task, snap)
    bits = [a]
    for cmd in extract_exec(a):
        bits.append(f"[EXEC] {cmd}")
        bits.append(run_exec(cmd, allow=True))
    return "\n".join(bits)


def plan_path(task: str) -> str:
    snap = read_snapshot_clip()
    return _ollama_plan(task, f"snapshot:\n{snap}")


def triple(task: str, advanced: bool = False, a_text: str | None = None) -> str:
    """A reflex -> B plan (or debate) -> C sheaf. B never sees the raw task alone."""
    t0 = time.time()
    snap = read_snapshot_clip()
    if a_text is None:
        a_text = _llama_chat_reflex(task, snap)
    execs = extract_exec(a_text)
    if advanced:
        b_raw = debate(task)
        try:
            b_text = json.loads(b_raw).get("triad", b_raw)
        except Exception:
            b_text = b_raw
        b_node = {"mode": "debate", "text": b_text}
    else:
        b_text = _ollama_plan(task, a_text)
        b_node = {"mode": "plan", "text": b_text}
    sheaf = sheaf_energy(a_text, b_text, execs)
    energy = float(sheaf["E(F)"])
    verdict = sheaf.get("verdict") or ("HALT" if energy > 0.0 else "NOMINAL")
    try:
        tel = json.loads(telemetry())
    except Exception as e:
        tel = {"error": str(e)}
    patch_snapshot(energy, verdict)
    allow = energy == 0.0
    if not allow:
        canary_append(f"SHEAF HALT E(F)={energy} task={task[:80]!r} execs={execs}")
        a_out = EXEC_RE.sub("EXEC: [stripped]", a_text)
        exec_results = ["HALT: EXEC stripped by sheaf"]
    else:
        a_out = a_text
        exec_results = [run_exec(c, allow=True) for c in execs]
    out = {
        "task": task,
        "advanced": advanced,
        "nodes": {
            "A_llama.cpp_8080": {"role": "fast_reflex", "text": a_out, "exec": execs, "exec_results": exec_results},
            "B_ollama_11434": b_node,
            "C_agi_cas": {"role": "sheaf_arbiter", "sheaf": sheaf, "telemetry": tel, "verdict": verdict},
        },
        "E(F)": energy,
        "verdict": verdict,
        "elapsed_sec": round(time.time() - t0, 2),
        "cloud_tokens": 0,
    }
    return json.dumps(out, default=str, indent=2)


def dispatch(kind: str, arg: str = "") -> str:
    k = (kind or "telemetry").strip().lower()
    if k in ("telemetry", "tel", "status"):
        return telemetry()
    if k in ("awareness", "audit"):
        return awareness(arg.strip() or "127.0.0.1")
    if k in ("supervisor", "cycle"):
        return supervisor()
    if k in ("debate", "triad", "agents"):
        return debate(arg or "assess local system")
    if k in ("research", "learn", "curiosity"):
        sys.path.insert(0, "/root/nexus_system")
        from nexus_curiosity_engine import execute_research
        return execute_research(arg or "local node")
    if k in ("cas_research", "loop"):
        return research(arg or "invariant_equilibrium")
    if k in ("fast", "!fast"):
        return fast_path(arg or "status")
    if k in ("plan", "!plan"):
        return plan_path(arg or "summarize local defense state")
    if k in ("triple", "simultaneous", "fanout"):
        return triple(arg or "local node status", advanced=False)
    if k in ("advanced", "deep", "sec", "!sec"):
        return triple(arg or "local node status", advanced=True)
    return f"unknown AGI op {kind}. use telemetry|awareness|supervisor|debate|research|fast|plan|triple|advanced"
