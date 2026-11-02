# Tools Hub

<img src="docs/readme-icon.png" width="96" align="right" alt="Tools Hub icon">

One window for a folder of small personal tools: a card per tool with a one-line status, and buttons to
open the tool, its folder or its backlog. The tools are listed in a registry file, `tools.json`.

## Status

1.0.0. Used daily on Ubuntu with a private registry. This repository ships an example registry with three
made-up tools; replace it with your own. The tests run in CI on every push.

## What it does

- Reads the registry `tools.json`: id, name, group, folder, how to open it, repo, and how to find its status.
- Shows one card per tool, grouped, with a coloured status dot (ok, warn, fail, off, stale, unknown).
- Finds each status in the background, at start and every 10 minutes:

  | `status` in tools.json | Where the line comes from |
  |---|---|
  | `summary` | The tool's own `<shared_dir>/<id>.json`; older than 2 days is marked stale |
  | `web` | An HTTP check of the tool's `url`; a local server that is down shows as off |
  | `files` | The newest file time under the listed `files`, or the tool's folder |
  | `git` | The last commit of the tool's folder, and whether it has uncommitted changes |
  | `netusage` | `netusage bill --json`, for a home internet usage tool with that command |
  | `doctor` | The last line of `~/.config/laptop-doctor/history.jsonl`, for a machine health tool |

- Publishes what it found for tools that do not publish themselves, so other tools can read it from the
  shared folder too.
- Writes `TOOLS.md` (an overview of every tool) next to the `tools-hub` folder each time it starts.
- `hub.install` puts the icons in the icon theme, names and icons on the Desktop and menu launchers,
  folder icons in Files, the Tools Hub launcher, and writes TOOLS.md. Safe to run again.

## What it does not do

- It does not run, update or fix the tools; it only opens them and reads their status.
- It does not edit backlogs; the Backlog button opens `backlogs/<id>.md` in the default editor.
- No notifications: a tool going to warn or fail shows only when the window is open.
- A tool missing from `tools.json` does not appear. Add it there, then add `backlogs/<id>.md`.
- Linux with a GNOME-style desktop only (`xdg-open`, `gio`, `.desktop` files).

## Install

Needs Python 3.12+ and [uv](https://docs.astral.sh/uv/). The hub expects to live in a folder of tools,
for example `~/My-Tools/tools-hub`, with the shared summaries in `~/My-Tools/shared-data`.

```sh
git clone <this repository> ~/My-Tools/tools-hub
cd ~/My-Tools/tools-hub
uv sync
```

Edit `tools.json` for your tools, add a `backlogs/<id>.md` per tool and, if you like, an icon
`assets/icons/<id>.png`. A registry entry:

```json
{"id": "photo-sorter", "name": "Photo Sorter", "group": "Files", "what": "Sorts camera photos",
 "path": "~/My-Tools/photo-sorter", "open": ["xdg-open", "~/My-Tools/photo-sorter"],
 "desktop": null, "repo": "local only", "status": "git"}
```

`web` entries also need a `url`; `files` entries can list `files`. A leading `~` is expanded.

## Run

```sh
uv run --project ~/My-Tools/tools-hub python -m hub          # the window
uv run --project ~/My-Tools/tools-hub python -m hub.install  # icons, launchers, TOOLS.md
```

The menu and Desktop entry `tools-hub.desktop` runs the first command.

## Files

| Path | What it is |
|---|---|
| `tools.json` | The registry (an example here). Edit this, not TOOLS.md |
| `backlogs/<id>.md` | One backlog per tool |
| `hub/registry.py` | Loads the registry, writes TOOLS.md |
| `hub/status.py` | The status probes and the shared summary format |
| `hub/collect.py` | Runs the right probe per tool; one failing probe never hides the others |
| `hub/app.py` | The PySide6 window |
| `hub/install.py`, `hub/icons.py` | Icons and launchers |
| `assets/icons/` | The hub's own icons; add one per tool |

The shared summary format, for a tool that wants to publish its own line:

```json
{"tool": "<id>", "updated": 1793548283.4, "level": "ok", "headline": "One line", "details": ["More"], "data": {}}
```

`updated` is a Unix time in seconds; `level` is one of ok, warn, fail, off, stale, unknown.

## Develop

```sh
uv run python -m pytest -q
```

Tests run Qt offscreen and never call the real `netusage`, network or git of other tools. They use the
shipped `tools.json`, whatever number of tools it lists.

## License

MIT, see [LICENSE](LICENSE).

## Author

Designed and built by Abdel Rahman Mohamad EL-Sayed ([AbdelRahman-Madboly](https://github.com/AbdelRahman-Madboly) on GitHub).
