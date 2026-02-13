"""File input orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from csvsafe.core.converter import convert_to_workbook
from csvsafe.core.parser import parse_csv
from csvsafe.core.writer import InputSource, write_and_open
from csvsafe.errors import CSVSafeError
from csvsafe.platform import macos

Notifier = Callable[[str, str], None]


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def handle_file(path: str, output_path: str | None = None, notifier: Notifier | None = None) -> Path | None:
    notify = notifier or (lambda title, message: macos.notify(title, message, level="error"))

    source_path = Path(path)
    if not source_path.exists() or not source_path.is_file():
        notify("CSVSafe", f"File not found: {source_path.name}")
        return None

    try:
        text = _read_text_file(source_path)
        parsed = parse_csv(text)
        workbook = convert_to_workbook(parsed, sheet_name=source_path.stem)
        output = write_and_open(workbook, InputSource(origin="file", source_path=source_path), output_path)
    except CSVSafeError as exc:
        notify("CSVSafe", exc.message)
        return None
    except OSError as exc:
        notify("CSVSafe", f"Could not read file: {source_path.name} ({exc})")
        return None
    except Exception as exc:  # pragma: no cover - defensive path
        notify("CSVSafe", f"Conversion failed: {exc}")
        return None

    for warning in parsed.warnings:
        macos.notify("CSVSafe", warning, level="warning")

    return output
