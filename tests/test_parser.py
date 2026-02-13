from __future__ import annotations

from pathlib import Path

import pytest

from csvsafe.core.parser import parse_csv
from csvsafe.errors import CSVSafeError

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_comma_delimited_parses():
    result = parse_csv(_read("simple.csv"))
    rows = list(result.rows)
    assert result.delimiter == ","
    assert rows[1][1] == "001"


def test_tab_delimited_detected():
    result = parse_csv(_read("tabs.tsv"))
    rows = list(result.rows)
    assert result.delimiter == "\t"
    assert rows[1] == ["alice", "001"]


def test_semicolon_delimited_detected():
    result = parse_csv(_read("semicolons.csv"))
    rows = list(result.rows)
    assert result.delimiter == ";"
    assert rows[2][0] == "bob"


def test_empty_input_errors():
    with pytest.raises(CSVSafeError):
        parse_csv("   \n")


def test_non_text_input_errors():
    with pytest.raises(CSVSafeError):
        parse_csv(123)  # type: ignore[arg-type]


def test_sniffer_failure_falls_back_to_comma():
    result = parse_csv("justonestringwithoutdelimiter")
    rows = list(result.rows)
    assert result.delimiter == ","
    assert rows == [["justonestringwithoutdelimiter"]]
    assert result.warnings


def test_result_rows_is_generator_and_list_of_strings():
    result = parse_csv(_read("simple.csv"))
    first = next(result.rows)
    assert isinstance(first, list)
    assert all(isinstance(item, str) for item in first)


def test_header_detection_boolean_present():
    result = parse_csv(_read("simple.csv"))
    assert isinstance(result.has_header, bool)
