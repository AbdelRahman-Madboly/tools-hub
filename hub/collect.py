"""Collect every tool's status, and publish what the Hub found for tools that do not publish themselves."""
from pathlib import Path

from . import status
from .registry import Registry, Tool

DOCTOR_HISTORY = Path.home() / ".config" / "laptop-doctor" / "history.jsonl"


def one(tool: Tool, shared: Path, deps: dict | None = None) -> status.Status:
    deps = deps or {}
    kind = tool.status
    if kind == "summary":
        return status.read_summary(shared, tool.id)
    if kind == "netusage":
        return status.netusage(shared, runner=deps.get("runner", status.subprocess.run))
    if kind == "doctor":
        s = status.doctor(deps.get("doctor_history", DOCTOR_HISTORY))
    elif kind == "web":
        s = status.web(tool.url, opener=deps.get("opener", status._get))
    elif kind == "files":
        s = status.files(tool.files or [tool.path])
    else:
        s = status.git(tool.path, runner=deps.get("runner", status.subprocess.run))
    status.publish(shared, tool.id, s)
    return s


def every(reg: Registry, deps: dict | None = None) -> dict[str, status.Status]:
    out = {}
    for t in reg.tools:
        try:
            out[t.id] = one(t, reg.shared_dir, deps)
        except Exception as e:                       # one broken probe must not hide the rest
            out[t.id] = status.Status("unknown", "Could not read the status", [str(e)])
    return out
