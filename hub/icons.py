"""Icons for the tools: rounded tiles, the icon theme for menus and launchers, and folder icons in Files."""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

THEME = Path.home() / ".local" / "share" / "icons" / "hicolor"
SIZES = (48, 64, 128, 256, 512)


def tile(src: Path, out: Path, size: int = 512, radius: float = 0.22) -> Path:
    """A square picture (a phone app's launcher image) as a rounded tile like the generated icons."""
    im = Image.open(src).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius), fill=255)
    im.putalpha(mask)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return Path(out)


def install(src: Path, name: str, theme_dir: Path = THEME, refresh: bool = True) -> str:
    """Put the icon in the user's icon theme under `name`, so launchers can say Icon=<name>."""
    im = Image.open(src).convert("RGBA")
    for n in SIZES:
        d = Path(theme_dir) / f"{n}x{n}" / "apps"
        d.mkdir(parents=True, exist_ok=True)
        im.resize((n, n), Image.LANCZOS).save(d / f"{name}.png")
    if refresh:
        subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(theme_dir)], capture_output=True)
    return name


def set_folder_icon(folder: Path, icon: Path, runner=subprocess.run) -> None:
    """The icon Files shows for a folder (GNOME keeps it as file metadata, nothing is written inside)."""
    runner(["gio", "set", str(folder), "metadata::custom-icon", Path(icon).as_uri()], check=False)
