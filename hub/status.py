"""Each tool's status line. A tool that publishes a summary in the shared folder is read from there;
for the others the Hub looks itself, and publishes what it found so other tools can read it too."""
import json
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

GB = 1024 ** 3
STALE_SECONDS = 2 * 86400


@dataclass(frozen=True)
class Status:
    level: str                  # ok | warn | fail | off | stale | unknown
    headline: str
    details: list[str] = field(default_factory=list)


def publish(shared: Path, tool_id: str, s: Status, data: dict | None = None) -> None:
    shared = Path(shared)
    shared.mkdir(parents=True, exist_ok=True)
    body = {"tool": tool_id, "updated": time.time(), "level": s.level, "headline": s.headline,
            "details": s.details, "data": data or {}}
    tmp = shared / f".{tool_id}.json.tmp"
    tmp.write_text(json.dumps(body, ensure_ascii=False, indent=2))
    tmp.replace(shared / f"{tool_id}.json")


def read_summary(shared: Path, tool_id: str) -> Status:
    f = Path(shared) / f"{tool_id}.json"
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError):
        return Status("unknown", "No summary yet. Open the tool once.")
    age = time.time() - float(d.get("updated", 0))
    if age > STALE_SECONDS:
        return Status("stale", d.get("headline", ""), [f"Not updated for {age / 86400:.0f} days"] + d.get("details", []))
    return Status(d.get("level", "ok"), d.get("headline", ""), list(d.get("details", [])))


def netusage(shared: Path, runner=subprocess.run) -> Status:
    """Internet Usage: this cycle's GB against what was bought, and the work share."""
    try:
        out = runner(["netusage", "bill", "--json"], capture_output=True, text=True, timeout=60)
        d = json.loads(out.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return Status("fail", "netusage did not answer", [str(e)])
    used = sum(d.get("parts", {}).values()) / GB
    bought = float(d.get("gb_bought") or 0)
    laptop = d["laptop_bytes"] / GB
    per_gb = d["cost_egp"] / bought if bought else 0
    s = Status("warn" if bought and used > 0.9 * bought else "ok",
               f"{used:.1f} of {bought:g} GB this cycle" if bought else f"{used:.1f} GB this cycle",
               [f"Cycle {d['cycle_start']} to {d['cycle_end']}",
                f"Laptop {laptop:.1f} GB · Work share E£{round(laptop * per_gb, 2):,.2f}"])
    publish(shared, "internet-usage", s, d)
    return s


def doctor(history: Path) -> Status:
    """Laptop Doctor: the last health check it recorded."""
    try:
        last = json.loads(Path(history).read_text().strip().splitlines()[-1])
    except (OSError, ValueError, IndexError):
        return Status("unknown", "No health check recorded yet")
    bad = [k for k, v in last.get("checks", {}).items() if v != "OK"]
    level = {"OK": "ok", "WARN": "warn", "FAIL": "fail"}.get(last.get("status"), "unknown")
    when = datetime.fromtimestamp(last["t"]).strftime("%d %b %H:%M")
    return Status(level, f"Health {last.get('score', '?')}/100", [
        ("Needs attention: " + ", ".join(bad)) if bad else "All checks OK", f"Checked {when}"])


def _get(url: str, timeout: float) -> int:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status


def web(url: str, opener=_get) -> Status:
    try:
        code = opener(url, 5)
    except OSError as e:
        local = "127.0.0.1" in url or "localhost" in url
        return Status("off" if local else "fail", "Server not running" if local else "Site not reachable", [str(e)])
    return Status("ok" if code < 400 else "fail", "Running" if code < 400 else f"Answered {code}", [url])


def files(paths: list[Path]) -> Status:
    newest = 0.0
    for p in paths:
        p = Path(p)
        items = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and ".git" not in f.parts][:5000]
        for f in items:
            try:
                newest = max(newest, f.stat().st_mtime)
            except OSError:
                pass
    if not newest:
        return Status("unknown", "No files yet")
    return Status("ok", f"Last change {datetime.fromtimestamp(newest):%d %b %Y %H:%M}")


def git(path: Path, runner=subprocess.run) -> Status:
    try:
        out = runner(["git", "-C", str(path), "log", "-1", "--format=%cd|%s", "--date=format:%d %b %Y"],
                     capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        out = ""
    if not out:
        return files([path])
    day, subject = out.split("|", 1)
    dirty = runner(["git", "-C", str(path), "status", "--porcelain"], capture_output=True, text=True,
                   timeout=10).stdout.strip()
    return Status("ok", f"Last change {day}", [subject] + (["Uncommitted changes"] if dirty else []))
