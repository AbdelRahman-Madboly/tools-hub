"""Registry loading, status read from the shared folder, and TOOLS.md, on small made-up registries."""
import json
import subprocess
import time
from pathlib import Path

from hub import collect, registry, status


def _registry_file(tmp_path, tools):
    f = tmp_path / "tools.json"
    f.write_text(json.dumps({"shared_dir": "~/shared", "tools": tools}))
    return f


ONE = {"id": "alpha", "name": "Alpha", "group": "Money", "what": "Counts things", "path": "~/alpha",
       "open": ["~/alpha/bin/alpha", "gui"], "desktop": None, "repo": "local only", "status": "summary"}
TWO = {"id": "beta", "name": "Beta", "group": "Machine", "what": "Checks things", "path": "/opt/beta",
       "open": ["xdg-open", "https://beta.example/"], "desktop": "beta.desktop", "repo": "github.com/x/beta",
       "status": "files", "files": ["~/beta/data.json"], "url": "https://beta.example/"}


def test_load_expands_home_and_fills_optional_fields(tmp_path):
    reg = registry.load(_registry_file(tmp_path, [ONE, TWO]))
    a, b = reg.get("alpha"), reg.get("beta")
    assert a.path == Path.home() / "alpha" and a.open == [str(Path.home() / "alpha/bin/alpha"), "gui"]
    assert a.url is None and a.files == [] and a.desktop is None
    assert b.path == Path("/opt/beta") and b.files == [Path.home() / "beta/data.json"]
    assert b.open[1] == "https://beta.example/" and b.url == "https://beta.example/"
    assert reg.shared_dir == Path.home() / "shared"


def test_tools_md_groups_in_registry_order_and_hides_the_home_folder(tmp_path):
    reg = registry.load(_registry_file(tmp_path, [ONE, TWO]))
    out = tmp_path / "TOOLS.md"
    registry.write_tools_md(reg, out, tmp_path / "backlogs")
    text = out.read_text()
    assert text.index("## Money") < text.index("## Machine")
    assert "`~/alpha`" in text and str(Path.home()) not in text
    assert "[backlogs/alpha.md](tools-hub/backlogs/alpha.md)" in text
    assert "edit that file, not this one" in text


def test_a_published_summary_reads_back_and_leaves_no_temp_file(tmp_path):
    status.publish(tmp_path, "alpha", status.Status("warn", "Two things", ["one", "two"]), {"n": 2})
    assert [p.name for p in tmp_path.iterdir()] == ["alpha.json"]
    assert json.loads((tmp_path / "alpha.json").read_text())["data"] == {"n": 2}
    assert status.read_summary(tmp_path, "alpha") == status.Status("warn", "Two things", ["one", "two"])


def test_a_broken_or_odd_summary_is_unknown_not_a_crash(tmp_path):
    (tmp_path / "a.json").write_text("{not json")
    (tmp_path / "b.json").write_text("[1, 2]")
    (tmp_path / "c.json").write_text(json.dumps({"updated": "2026-10-27T10:00", "headline": "x"}))
    (tmp_path / "d.json").write_text(json.dumps({"updated": time.time(), "level": "great", "headline": "x"}))
    assert status.read_summary(tmp_path, "a").level == "unknown"
    assert status.read_summary(tmp_path, "b").headline == "Summary file is not readable"
    assert status.read_summary(tmp_path, "c").level == "unknown"
    assert status.read_summary(tmp_path, "d").level == "unknown"


def test_a_summary_without_details_or_level_is_ok(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps({"updated": time.time(), "headline": "Fine"}))
    assert status.read_summary(tmp_path, "a") == status.Status("ok", "Fine", [])


def test_git_status_names_the_last_commit_and_uncommitted_work(tmp_path):
    def runner(cmd, **kw):
        out = "01 Nov 2026|feat: thing" if "log" in cmd else " M file.py\n"
        return subprocess.CompletedProcess(cmd, 0, out, "")
    s = status.git(tmp_path, runner=runner)
    assert s.headline == "Last change 01 Nov 2026" and s.details == ["feat: thing", "Uncommitted changes"]


def test_git_status_falls_back_to_file_times_outside_a_repo(tmp_path):
    (tmp_path / "x.txt").write_text("x")
    s = status.git(tmp_path, runner=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 128, "", "not a repo"))
    assert s.level == "ok" and s.headline.startswith("Last change")


def test_one_broken_probe_does_not_hide_the_others(tmp_path):
    bad = dict(ONE, id="bad", status="doctor")
    reg = registry.load(_registry_file(tmp_path, [ONE, bad]))
    reg = registry.Registry(reg.tools, tmp_path / "shared")
    hist = tmp_path / "history.jsonl"
    hist.write_text(json.dumps({"score": 1}) + "\n")       # no timestamp: the doctor probe fails
    got = collect.every(reg, {"doctor_history": hist})
    assert got["alpha"].level == "unknown" and got["bad"].headline == "Could not read the status"
