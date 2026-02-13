"""Workbook output handling."""

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from openpyxl import Workbook

from csvsafe.platform import macos


@dataclass
class InputSource:
    origin: Literal["file", "clipboard"]
    source_path: Path | None = None


def _next_available_path(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path

    index = 1
    while True:
        candidate = base_path.with_name(f"{base_path.stem} ({index}){base_path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _default_output_path(source: InputSource) -> Path:
    if source.origin == "file":
        if source.source_path is None:
            raise ValueError("source_path is required for file origin")
        return _next_available_path(source.source_path.with_suffix(".xlsx"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / f"CSVSafe_clipboard_{timestamp}.xlsx"


def _set_readonly(path: Path) -> None:
    mode = path.stat().st_mode
    mode &= ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    os.chmod(path, mode)


def write_and_open(
    workbook: Workbook,
    source: InputSource,
    output_path: str | Path | None = None,
) -> Path:
    destination = Path(output_path) if output_path is not None else _default_output_path(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    workbook.save(destination)

    if source.origin == "clipboard" and output_path is None:
        _set_readonly(destination)

    macos.open_file(destination)
    return destination
