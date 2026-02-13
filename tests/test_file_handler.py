from __future__ import annotations

from pathlib import Path

from csvsafe.input.file_handler import handle_file


def test_valid_csv_file_processed(tmp_path: Path, monkeypatch):
    source = tmp_path / "example.csv"
    source.write_text("name,id\nalice,001\n", encoding="utf-8")

    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    out = handle_file(str(source))
    assert out is not None
    assert out.exists()


def test_nonexistent_file_notifies_and_returns_none(monkeypatch):
    messages: list[str] = []

    def fake_notify(_title: str, message: str) -> None:
        messages.append(message)

    out = handle_file("/no/such/file.csv", notifier=fake_notify)
    assert out is None
    assert any("File not found" in m for m in messages)


def test_latin1_file_fallback(tmp_path: Path, monkeypatch):
    source = tmp_path / "latin.csv"
    source.write_bytes("name\nJos\xe9\n".encode("latin-1"))

    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    out = handle_file(str(source))
    assert out is not None
