"""CSVSafe command line interface."""

from __future__ import annotations

import argparse
import sys

from csvsafe.input.clipboard_handler import handle_clipboard
from csvsafe.input.file_handler import handle_file


def _cli_notify(title: str, message: str) -> None:
    del title
    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="csvsafe")
    subparsers = parser.add_subparsers(dest="command")

    convert_parser = subparsers.add_parser("convert", help="Convert one CSV/TSV file")
    convert_parser.add_argument("input", help="Input CSV/TSV path")
    convert_parser.add_argument("-o", "--output", help="Output XLSX path")

    clipboard_parser = subparsers.add_parser("clipboard", help="Convert clipboard text")
    clipboard_parser.add_argument("-o", "--output", help="Output XLSX path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "convert":
        result = handle_file(args.input, output_path=args.output, notifier=_cli_notify)
        if result is None:
            return 1
        print(result)
        return 0

    if args.command == "clipboard":
        result = handle_clipboard(output_path=args.output, notifier=_cli_notify)
        if result is None:
            return 1
        print(result)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
