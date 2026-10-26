"""Install the suite's look: icons in the theme, names and icons on every launcher (Desktop and menu),
folder icons in Files, the Tools Hub launcher, and TOOLS.md. Safe to run again: uv run python -m hub.install"""
import re
import shutil
from pathlib import Path

from . import icons, registry

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
DESKTOP = HOME / "Desktop"
MENU = HOME / ".local" / "share" / "applications"
MY_TOOLS = HOME / "My-Tools"


def rewrite_entry(text: str, name: str, icon: str) -> str:
    """Name= and Icon= of the main [Desktop Entry] group only; actions and everything else stay."""
    head, sep, rest = text.partition("\n[Desktop Action")
    head = re.sub(r"^Name=.*$", f"Name={name}", head, count=1, flags=re.M)
    if re.search(r"^Icon=", head, flags=re.M):
        head = re.sub(r"^Icon=.*$", f"Icon={icon}", head, count=1, flags=re.M)
    else:
        head = head.rstrip("\n") + f"\nIcon={icon}\n"
    return head + sep + rest


def _exec(text: str) -> str | None:
    m = re.search(r"^Exec=(.*)$", text.partition("\n[Desktop Action")[0], flags=re.M)
    return m.group(1).strip() if m else None


def same_exec(folder: Path, exec_line: str) -> list[Path]:
    return [f for f in sorted(Path(folder).glob("*.desktop")) if _exec(f.read_text()) == exec_line]


HUB_ENTRY = """[Desktop Entry]
Type=Application
Name=Tools Hub
Comment=Open every tool, see its status and follow its backlog
Exec={uv} run --project {root} python -m hub
Path={root}
Icon=mytools-tools-hub
Terminal=false
Categories=Utility;
StartupWMClass=tools-hub
"""


def main() -> int:
    reg = registry.load(ROOT / "tools.json")
    art = ROOT / "assets" / "icons"
    for src in sorted(art.glob("*.png")):
        icons.install(src, f"mytools-{src.stem}", refresh=False)
    icons.install(art / "tools-hub.png", "mytools-tools-hub") if (art / "tools-hub.png").exists() else None

    for t in reg.tools:
        icon = f"mytools-{t.id}"
        if (art / f"{t.id}.png").exists():
            icons.set_folder_icon(t.path, art / f"{t.id}.png")
        if t.desktop and (DESKTOP / t.desktop).exists():
            f = DESKTOP / t.desktop
            text = f.read_text()
            for menu in same_exec(MENU, _exec(text) or ""):
                menu.write_text(rewrite_entry(menu.read_text(), t.name, icon))
            f.write_text(rewrite_entry(text, t.name, icon))
            print(f"launcher  {t.name}")
    for folder, art_name in ((MY_TOOLS, "my-tools"), (MY_TOOLS / "shared-data", "shared-data"),
                             (ROOT, "tools-hub")):
        if (art / f"{art_name}.png").exists():
            icons.set_folder_icon(folder, art / f"{art_name}.png")

    local = HOME / ".local" / "bin" / "uv"           # never a tool shim from the shell running the install
    uv = str(local) if local.exists() else (shutil.which("uv") or "uv")
    entry = HUB_ENTRY.format(uv=uv, root=ROOT)
    for target in (MENU / "tools-hub.desktop", DESKTOP / "tools-hub.desktop"):
        target.write_text(entry)
        target.chmod(0o755)
    icons.subprocess.run(["gio", "set", str(DESKTOP / "tools-hub.desktop"), "metadata::trusted", "true"],
                         capture_output=True)
    icons.subprocess.run(["update-desktop-database", str(MENU)], capture_output=True)
    registry.write_tools_md(reg, MY_TOOLS / "TOOLS.md", ROOT / "backlogs")
    print("Tools Hub, icons and TOOLS.md installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
