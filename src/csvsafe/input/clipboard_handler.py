"""Clipboard input orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from csvsafe.core.converter import convert_to_workbook
from csvsafe.core.parser import parse_csv
from csvsafe.core.writer import InputSource, write_and_open
from csvsafe.errors import CSVSafeError
from csvsafe.platform import macos

Notifier = Callable[[str, str], None]


def handle_clipboard(output_path: str | None = None, notifier: Notifier | None = None) -> Path | None:
    notify = notifier or (lambda title, message: macos.notify(title, message, level="error"))

    try:
        clipboard = macos.read_clipboard_text()
    except Exception as exc:
        notify("CSVSafe", f"Could not read clipboard: {exc}")
        return None

    if not clipboard.is_text or not clipboard.text.strip():
        notify("CSVSafe", "No CSV data found on clipboard")
        return None

    try:
        parsed = parse_csv(clipboard.text)
        workbook = convert_to_workbook(parsed, sheet_name="Clipboard")
        output = write_and_open(workbook, InputSource(origin="clipboard"), output_path)
    except CSVSafeError as exc:
        notify("CSVSafe", exc.message)
        return None
    except Exception as exc:  # pragma: no cover - defensive path
        notify("CSVSafe", f"Clipboard conversion failed: {exc}")
        return None

    for warning in parsed.warnings:
        macos.notify("CSVSafe", warning, level="warning")

    return output
