"""CSV parser with delimiter/header detection."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from typing import Generator

from csvsafe.errors import CSVSafeError


@dataclass
class ParseResult:
    rows: Generator[list[str], None, None]
    delimiter: str
    has_header: bool
    warnings: list[str] = field(default_factory=list)


def parse_csv(text: str) -> ParseResult:
    if not isinstance(text, str):
        raise CSVSafeError("Could not parse CSV data")

    normalized = text.lstrip("\ufeff")
    if not normalized.strip():
        raise CSVSafeError("No CSV data found")

    sample = normalized[:8192]
    sniffer = csv.Sniffer()
    warnings: list[str] = []
    dialect = None

    try:
        dialect = sniffer.sniff(sample)
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
        warnings.append("Could not detect delimiter; using comma.")

    try:
        has_header = sniffer.has_header(sample)
    except csv.Error:
        has_header = False
        warnings.append("Could not detect header row.")

    def row_generator() -> Generator[list[str], None, None]:
        buffer = StringIO(normalized)
        reader: csv.reader
        if dialect is not None:
            reader = csv.reader(buffer, dialect=dialect)
        else:
            reader = csv.reader(buffer, delimiter=delimiter)

        try:
            for row in reader:
                yield [str(cell) for cell in row]
        except csv.Error as exc:
            raise CSVSafeError("Could not parse CSV data") from exc

    return ParseResult(
        rows=row_generator(),
        delimiter=delimiter,
        has_header=has_header,
        warnings=warnings,
    )
