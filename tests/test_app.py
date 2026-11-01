import json
import os
import subprocess
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from hub import app, collect, registry, status

ROOT = Path(__file__).resolve().parent.parent
_APP = None


def _reg(tmp_path):
    reg = registry.load(ROOT / "tools.json")
    return registry.Registry(reg.tools, tmp_path / "shared")


def _deps(tmp_path):
    out = {"cycle_start": "2026-09-27", "cycle_end": "2026-10-27", "laptop_bytes": 1, "parts": {"Laptop": 1},
           "gb_bought": 510.0, "cost_egp": 510.0}
    h = tmp_path / "history.jsonl"
    h.write_text(json.dumps({"t": time.time(), "score": 94, "status": "WARN", "checks": {"memory": "WARN"}}) + "\n")
    return {"runner": lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, json.dumps(out) if cmd[0] == "netusage" else "", ""),
            "opener": lambda url, timeout: 200, "doctor_history": h}


def test_every_tool_gets_a_status_and_the_hub_publishes_the_ones_it_found(tmp_path):
    reg = _reg(tmp_path)
    got = collect.every(reg, _deps(tmp_path))
    assert set(got) == {t.id for t in reg.tools}
    assert got["web-dashboard"].headline == "Running"
    assert (reg.shared_dir / "web-dashboard.json").exists() and (reg.shared_dir / "photo-sorter.json").exists()
    assert got["budget-notes"].level == "unknown"          # it publishes itself; none in this temp folder


def test_window_shows_a_card_per_tool_and_opens_them(tmp_path):
    global _APP
    _APP = QApplication.instance() or QApplication([])   # keep a reference: Qt must outlive the window
    launched = []
    w = app.HubWindow(_reg(tmp_path), ROOT, launcher=lambda argv: launched.append(argv))
    w.show_statuses(collect.every(w.reg, _deps(tmp_path)))
    assert set(w.cards) == {t.id for t in w.reg.tools}
    card = w.cards["web-dashboard"]
    assert "Running" in card.headline.text()
    card.btn_open.click()
    card.btn_backlog.click()
    assert launched[0] == w.reg.get("web-dashboard").open
    assert launched[1] == ["xdg-open", str(ROOT / "backlogs" / "web-dashboard.md")]
    w.close()
    w.deleteLater()
    _APP.processEvents()
