# CSVSafe

CSVSafe is a macOS menu bar app and CLI that converts CSV/TSV data into XLSX with every cell formatted as text, preventing spreadsheet auto-coercion issues.

## Features

- Converts `.csv` and `.tsv` files to `.xlsx`
- Clipboard to read-only temp `.xlsx`
- Menu bar app for quick conversion
- CLI for automation

## Quick Start

```bash
python3.11 -m venv .venv
source .venv/bin/activate
make install
make test
```

## Run

```bash
.venv/bin/csvsafe convert /path/to/input.csv
.venv/bin/csvsafe clipboard
.venv/bin/csvsafe-menubar
```

## License

MIT
