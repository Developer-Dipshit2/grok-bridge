#!/usr/bin/env python3
"""Grok-CLI-parity tools. All execution is local. No cloud."""
from __future__ import annotations

import glob as globmod
import os
import re
import subprocess
from pathlib import Path
from typing import List

WORKDIR = os.environ.get("LOCAL_GROK_WORKDIR", "/root")
STATE = Path("/root/local_grok/state")
PLAN = STATE / "plan.md"
MAX_READ = 80_000
MAX_WRITE = 400_000
SHELL_TIMEOUT = 60
BLOCKED = ("rm -rf /", "rm -rf /*", "mkfs", "> /dev/block", "dd if=", ":(){")


def _root(path: str) -> Path:
    p = Path(path or ".").expanduser()
    if not p.is_absolute():
        p = Path(WORKDIR) / p
    return p.resolve()


def read_file(path: str) -> str:
    p = _root(path)
    if not p.exists():
        return f"ERROR: not found: {p}"
    if p.is_dir():
        names = sorted(os.listdir(p))[:200]
        return f"DIR {p}\n" + "\n".join(names)
    data = p.read_text(encoding="utf-8", errors="replace")
    if len(data) > MAX_READ:
        return data[:MAX_READ] + f"\n...[truncated]"
    return data


def write(path: str, content: str) -> str:
    if len(content) > MAX_WRITE:
        return "ERROR: write too large"
    p = _root(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"WROTE {p} ({len(content)} bytes)"


def str_replace(path: str, old: str, new: str) -> str:
    p = _root(path)
    if not p.is_file():
        return f"ERROR: not a file: {p}"
    text = p.read_text(encoding="utf-8", errors="replace")
    n = text.count(old)
    if n == 0:
        return "ERROR: old_string not found"
    if n > 1:
        return f"ERROR: old_string found {n} times; make it unique"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    return f"UPDATED {p}"


def bash(cmd: str, readonly: bool = False) -> str:
    c = (cmd or "").strip()
    if not c:
        return "ERROR: empty command"
    low = c.lower()
    if any(b in low for b in BLOCKED):
        return "ERROR: blocked"
    if readonly and any(x in low for x in ("rm ", "mv ", "dd ", "mkfs", ">", "tee ")):
        return "ERROR: mutating shell forbidden in this mode"
    try:
        res = subprocess.run(
            c, shell=True, cwd=WORKDIR, capture_output=True, text=True, timeout=SHELL_TIMEOUT
        )
        out = (res.stdout or "") + (("\n" + res.stderr) if res.stderr else "")
        return f"exit={res.returncode}\n{out[-12000:]}".strip()
    except subprocess.TimeoutExpired:
        return "ERROR: shell timeout"
    except Exception as e:
        return f"ERROR: {e}"


def grep(pattern: str, path: str = ".") -> str:
    p = _root(path or ".")
    try:
        res = subprocess.run(
            ["rg", "-n", "--max-count", "40", pattern, str(p)],
            capture_output=True, text=True, timeout=15,
        )
        out = res.stdout or res.stderr or ""
        return out[-8000:] or "(no matches)"
    except FileNotFoundError:
        res = subprocess.run(
            ["grep", "-R", "-n", "-E", pattern, str(p)],
            capture_output=True, text=True, timeout=15,
        )
        return (res.stdout or res.stderr or "")[-8000:] or "(no matches)"
    except Exception as e:
        return f"ERROR: {e}"


def glob_search(pattern: str) -> str:
    hits = globmod.glob(str(_root(pattern)), recursive=True)[:80]
    return "\n".join(hits) or "(no matches)"


def list_dir(path: str = ".") -> str:
    return read_file(path)


def plan_read() -> str:
    STATE.mkdir(parents=True, exist_ok=True)
    if not PLAN.exists():
        return "(empty plan)"
    return PLAN.read_text(encoding="utf-8")


def plan_write(content: str) -> str:
    STATE.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(content, encoding="utf-8")
    return f"WROTE {PLAN}"


def agi(kind: str, arg: str = "") -> str:
    from agi_bridge import dispatch
    return dispatch(kind, arg)


def execute(tool: str, args: dict, mode: str) -> str:
    t = (tool or "").lower()
    readonly = mode in ("ask", "review", "plan")
    if t in ("read_file", "read"):
        return read_file(args.get("path") or args.get("arg") or "")
    if t in ("write",):
        if readonly and mode != "plan":
            return "ERROR: write forbidden in this mode"
        if mode == "plan":
            return plan_write(args.get("content") or args.get("text") or "")
        return write(args.get("path") or "", args.get("content") or args.get("text") or "")
    if t in ("str_replace", "strreplace"):
        if readonly:
            return "ERROR: write forbidden"
        return str_replace(args.get("path") or "", args.get("old") or "", args.get("new") or "")
    if t in ("bash", "shell"):
        return bash(args.get("cmd") or args.get("command") or args.get("arg") or "", readonly=readonly)
    if t == "grep":
        return grep(args.get("pattern") or args.get("arg") or "", args.get("path") or ".")
    if t in ("glob", "list_dir", "list"):
        if t == "glob":
            return glob_search(args.get("pattern") or args.get("arg") or "*")
        return list_dir(args.get("path") or args.get("arg") or ".")
    if t in ("plan_write",):
        return plan_write(args.get("content") or args.get("text") or "")
    if t in ("plan_read",):
        return plan_read()
    if t == "agi":
        return agi(args.get("kind") or args.get("op") or "telemetry", args.get("arg") or args.get("task") or "")
    return f"ERROR: unknown tool {tool}"
