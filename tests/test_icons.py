from PIL import Image

from hub import icons


def test_a_square_picture_becomes_a_rounded_512_icon(tmp_path):
    src = tmp_path / "in.png"
    Image.new("RGB", (192, 192), (200, 30, 30)).save(src)
    out = icons.tile(src, tmp_path / "out.png")
    im = Image.open(out)
    assert im.size == (512, 512) and im.mode == "RGBA"
    assert im.getpixel((0, 0))[3] == 0 and im.getpixel((256, 256))[3] == 255


def test_install_puts_sizes_in_the_icon_theme(tmp_path):
    src = tmp_path / "x.png"
    Image.new("RGBA", (1024, 1024), (10, 200, 10, 255)).save(src)
    names = icons.install(src, "mytools-x", theme_dir=tmp_path / "hicolor", refresh=False)
    assert (tmp_path / "hicolor" / "256x256" / "apps" / "mytools-x.png").exists()
    assert names == "mytools-x"


def test_folder_icon_is_set_through_gio(tmp_path):
    calls = []
    icons.set_folder_icon(tmp_path, tmp_path / "i.png", runner=lambda argv, **kw: calls.append(argv))
    assert calls == [["gio", "set", str(tmp_path), "metadata::custom-icon", (tmp_path / "i.png").as_uri()]]
