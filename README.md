# Tools Hub

One window that lists every personal tool in `~/My-Tools` (and tools that live elsewhere),
shows a one-line status for each, and opens the tool, its folder or its backlog.

**Status:** 1.0.0, finished and in daily use. Private, local only, no remote.

## What it does

- Reads the registry `tools.json`: id, name, group, folder, how to open it, repo, and how to find its status.
- Shows one card per tool, grouped, with a coloured status dot (ok, warn, fail, off, stale, unknown).
- Finds each status in the background, at start and every 10 minutes:

  | `status` in tools.json | Where the line comes from |
  |---|---|
  | `summary` | The tool's own `shared-data/<id>.json`; older than 2 days is marked stale |
  | `netusage` | `netusage bill --json` (this cycle's GB and the work share) |
  | `doctor` | The last line of `~/.config/laptop-doctor/history.jsonl` |
  | `web` | An HTTP check of the tool's `url`; a local server that is down shows as off |
  | `files` | The newest file time under the listed files or folders |
  | `git` | The last commit of the tool's folder, and whether it has uncommitted changes |

- Publishes what it found for tools that do not publish themselves, so other tools can read it from
  `shared-data/` too.
- Writes `~/My-Tools/TOOLS.md` from the registry each time it starts.
- `hub.install` puts the icons in the icon theme, names and icons on the Desktop and menu launchers,
  folder icons in Files, the Tools Hub launcher, and writes TOOLS.md. Safe to run again.

## What it does not do

- It does not run, update or fix the tools; it only opens them and reads their status.
- It does not edit backlogs; the Backlog button opens `backlogs/<id>.md` in the default editor.
- No notifications: a tool going to warn or fail shows only when the window is open.
- A tool missing from `tools.json` does not appear. Add it there, then add `backlogs/<id>.md`.

## Run

```sh
uv run --project ~/My-Tools/tools-hub python -m hub      # the window
uv run --project ~/My-Tools/tools-hub python -m hub.install  # icons, launchers, TOOLS.md
```

The menu and Desktop entry `tools-hub.desktop` runs the first command.

## Files

| Path | What it is |
|---|---|
| `tools.json` | The registry. Edit this, not TOOLS.md |
| `backlogs/<id>.md` | One backlog per tool |
| `hub/registry.py` | Loads the registry, writes TOOLS.md |
| `hub/status.py` | The status probes and the shared summary format |
| `hub/collect.py` | Runs the right probe per tool; one failing probe never hides the others |
| `hub/app.py` | The PySide6 window |
| `hub/install.py`, `hub/icons.py` | Icons and launchers |
| `assets/icons/` | One icon per tool |

The shared summary format, for a tool that wants to publish its own line:

```json
{"tool": "<id>", "updated": 1793548283.4, "level": "ok", "headline": "One line", "details": ["More"], "data": {}}
```

`updated` is a Unix time in seconds; `level` is one of ok, warn, fail, off, stale, unknown.

## Develop

```sh
uv run python -m pytest -q
```

Tests run Qt offscreen and never call the real `netusage`, network or git of other tools. One test checks
the real `tools.json`: every tool has an existing folder and a backlog file.
