from hub import install


def test_a_launcher_gets_the_new_name_and_icon_and_keeps_everything_else():
    text = "[Desktop Entry]\nType=Application\nName=Net Usage\nExec=/usr/bin/x\nIcon=old\n\n[Desktop Action a]\nName=Keep me\n"
    out = install.rewrite_entry(text, "Internet Usage", "mytools-internet-usage")
    assert "Name=Internet Usage\n" in out and "Icon=mytools-internet-usage\n" in out
    assert "Exec=/usr/bin/x" in out and "Name=Keep me" in out and "Net Usage" not in out


def test_an_entry_without_an_icon_gets_one():
    out = install.rewrite_entry("[Desktop Entry]\nName=A\nExec=b\n", "A", "mytools-a")
    assert "Icon=mytools-a" in out


def test_the_menu_copy_is_found_by_its_exec_line(tmp_path):
    (tmp_path / "x.desktop").write_text("[Desktop Entry]\nName=Old\nExec=/opt/run --flag\n")
    (tmp_path / "y.desktop").write_text("[Desktop Entry]\nName=Other\nExec=/opt/other\n")
    assert install.same_exec(tmp_path, "/opt/run --flag") == [tmp_path / "x.desktop"]
