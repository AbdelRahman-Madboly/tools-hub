import json
import os
import subprocess
import time
from pathlib import Path

from hub import registry, status

ROOT = Path(__file__).resolve().parent.parent


def test_registry_lists_every_tool_with_a_real_folder_and_a_backlog():
    reg = registry.load(ROOT / "tools.json")
    ids = [t.id for t in reg.tools]
    assert len(ids) == len(set(ids)) == 11
    for t in reg.tools:
        assert t.path.exists(), t.id
        assert "~" not in " ".join(t.open)
        assert (ROOT / "backlogs" / f"{t.id}.md").exists(), t.id
    assert reg.shared_dir == Path.home() / "My-Tools" / "shared-data"


def test_a_fresh_summary_is_shown_and_an_old_one_is_marked_stale(tmp_path):
    f = tmp_path / "budget-notes.json"
    f.write_text(json.dumps({"tool": "budget-notes", "updated": time.time(), "level": "warn",
                             "headline": "Two bills due this week", "details": ["Next one on Friday"]}))
    s = status.read_summary(tmp_path, "budget-notes")
    assert (s.level, s.headline, s.details) == ("warn", "Two bills due this week", ["Next one on Friday"])
    old = time.time() - 3 * 86400
    os.utime(f, (old, old))
    f.write_text(json.dumps({**json.loads(f.read_text()), "updated": old}))
    assert status.read_summary(tmp_path, "budget-notes").level == "stale"
    assert status.read_summary(tmp_path, "missing").level == "unknown"


def test_internet_status_from_netusage_and_it_is_published(tmp_path):
    out = {"cycle_start": "2026-09-27", "cycle_end": "2026-10-27", "laptop_bytes": 290 * 1024 ** 3,
           "parts": {"Laptop": 290 * 1024 ** 3, "Phone": 76 * 1024 ** 3}, "gb_bought": 510.0, "cost_egp": 510.0}
    runner = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, json.dumps(out), "")
    s = status.netusage(tmp_path, runner=runner)
    assert "366.0 of 510 GB" in s.headline and s.level == "ok"
    assert any("Work" in d and "290.00" in d for d in s.details)
    assert json.loads((tmp_path / "internet-usage.json").read_text())["headline"] == s.headline


def test_internet_status_when_netusage_is_missing(tmp_path):
    def gone(cmd, **kw):
        raise FileNotFoundError(cmd[0])
    assert status.netusage(tmp_path, runner=gone).level == "fail"


def test_doctor_status_from_its_history(tmp_path):
    h = tmp_path / "history.jsonl"
    h.write_text(json.dumps({"t": time.time(), "score": 88, "status": "WARN",
                             "checks": {"disk": "OK", "memory": "WARN", "crashes": "WARN"}}) + "\n")
    s = status.doctor(h)
    assert s.level == "warn" and "88" in s.headline and "memory" in s.details[0]


def test_web_status(tmp_path):
    assert status.web("https://x", opener=lambda url, timeout: 200).level == "ok"
    def down(url, timeout):
        raise OSError("refused")
    s = status.web("http://127.0.0.1:1/api/health", opener=down)
    assert s.level == "off" and "not running" in s.headline


def test_files_status_names_the_newest_change(tmp_path):
    (tmp_path / "a.json").write_text("{}")
    s = status.files([tmp_path])
    assert s.level == "ok" and s.headline.startswith("Last change")


def test_tools_md_lists_every_tool(tmp_path):
    reg = registry.load(ROOT / "tools.json")
    out = tmp_path / "TOOLS.md"
    registry.write_tools_md(reg, out, ROOT / "backlogs")
    text = out.read_text()
    for t in reg.tools:
        assert t.name in text and f"backlogs/{t.id}.md" in text
