# Changelog

## Unreleased

- The registry is now an example with three made-up tools, with an example backlog each; the registry
  tests no longer expect a fixed number of tools or existing tool folders.
- MIT license, CI workflow that runs the tests on every push, README for a fresh install.

## 1.0.0 - 2026-11-01

- Registry of every tool in `tools.json`, TOOLS.md generated from it, one backlog per tool.
- Status per tool from its shared summary, netusage, Laptop Doctor history, a web check, file times or git.
- PySide6 window with a card per tool: open, folder, backlog; background refresh every 10 minutes.
- Icons, launchers and folder icons installed by `hub.install`.
- A summary file with the wrong shape (a list, a text date, an unknown level) now shows as unknown
  instead of failing the whole probe.
- Tests for registry loading, status reading, TOOLS.md, git status and probe isolation; README.
