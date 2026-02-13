from __future__ import annotations

from pathlib import Path

from csvsafe import cli
from csvsafe.platform.macos import ClipboardContent


def test_convert_subcommand(monkeypatch, tmp_path: Path):
    source = tmp_path / "input.csv"
    source.write_text("name,id\na,1\n", encoding="utf-8")

    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    code = cli.main(["convert", str(source)])
    assert code == 0


def test_convert_with_output(monkeypatch, tmp_path: Path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.xlsx"
    source.write_text("name,id\na,1\n", encoding="utf-8")

    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    code = cli.main(["convert", str(source), "-o", str(output)])
    assert code == 0
    assert output.exists()


def test_clipboard_subcommand(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "csvsafe.platform.macos.read_clipboard_text",
        lambda: ClipboardContent(is_text=True, text="a,b\n1,2\n"),
    )
    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    code = cli.main(["clipboard", "-o", str(tmp_path / "clip.xlsx")])
    assert code == 0


def test_invalid_path_returns_nonzero(monkeypatch):
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)
    code = cli.main(["convert", "/does/not/exist.csv"])
    assert code == 1


def test_missing_subcommand_returns_nonzero():
    code = cli.main([])
    assert code == 1
