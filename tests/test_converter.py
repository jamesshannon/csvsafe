from __future__ import annotations

from csvsafe.core.converter import convert_to_workbook
from csvsafe.core.parser import parse_csv


def test_all_cells_text_format_and_header_features():
    parsed = parse_csv("name,id\nalice,007\nbob,008\n")
    workbook = convert_to_workbook(parsed, sheet_name="Data")
    ws = workbook.active

    assert ws["A1"].font.bold is True
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref is not None

    for row in ws.iter_rows(min_row=1, max_row=3, min_col=1, max_col=2):
        for cell in row:
            assert cell.number_format == "@"


def test_no_header_features_when_has_header_false():
    parsed = parse_csv("007\n008\n")
    parsed.has_header = False
    workbook = convert_to_workbook(parsed)
    ws = workbook.active

    assert ws.freeze_panes is None
    assert ws.auto_filter.ref is None


def test_values_preserved():
    parsed = parse_csv("value\n007\n123456789012345\n3-5\n")
    workbook = convert_to_workbook(parsed)
    ws = workbook.active

    assert ws["A2"].value == "007"
    assert ws["A3"].value == "123456789012345"
    assert ws["A4"].value == "3-5"


def test_sheet_name_sanitized():
    parsed = parse_csv("a,b\n1,2\n")
    workbook = convert_to_workbook(parsed, sheet_name="Bad/Name*With:Chars?")
    assert workbook.active.title == "Bad_Name_With_Chars_"
