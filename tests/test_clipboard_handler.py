from __future__ import annotations

from csvsafe.platform.macos import ClipboardContent
from csvsafe.input.clipboard_handler import handle_clipboard


def test_valid_clipboard_processed(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "csvsafe.platform.macos.read_clipboard_text",
        lambda: ClipboardContent(is_text=True, text="name,id\nalice,001\n"),
    )
    monkeypatch.setattr("csvsafe.platform.macos.open_file", lambda _p: None)
    monkeypatch.setattr("csvsafe.platform.macos.notify", lambda *args, **kwargs: None)

    out = handle_clipboard(output_path=str(tmp_path / "out.xlsx"))
    assert out is not None
    assert out.exists()


def test_empty_clipboard_errors(monkeypatch):
    monkeypatch.setattr(
        "csvsafe.platform.macos.read_clipboard_text",
        lambda: ClipboardContent(is_text=True, text="   "),
    )
    messages: list[str] = []

    out = handle_clipboard(notifier=lambda _t, m: messages.append(m))
    assert out is None
    assert messages == ["No CSV data found on clipboard"]


def test_non_text_clipboard_errors(monkeypatch):
    monkeypatch.setattr(
        "csvsafe.platform.macos.read_clipboard_text",
        lambda: ClipboardContent(is_text=False, text=""),
    )
    messages: list[str] = []

    out = handle_clipboard(notifier=lambda _t, m: messages.append(m))
    assert out is None
    assert messages == ["No CSV data found on clipboard"]
