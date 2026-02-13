# CSVSafe — Development Plan

## Overview

CSVSafe is a macOS menubar application that converts CSV data into properly formatted XLSX files, preventing Excel's aggressive data munging (scientific notation, dropped leading zeros, date coercion, etc.). It provides a seamless, zero-friction workflow as a persistent menubar app with multiple input methods.

### The Problem

When Excel opens a CSV file (or receives CSV data from the clipboard), it applies automatic type inference that silently corrupts data: long numbers become scientific notation, leading zeros are stripped, strings like "3-5" become dates. This is irreversible on open and breaks downstream operations like VLOOKUP. The standard workaround — Excel's "Get Data" import wizard — requires per-column type specification and is impractical for routine work.

### The Solution

CSVSafe intercepts CSV/TSV data before spreadsheet software can coerce it, converts all cells to text-formatted XLSX, and opens the result using the system default `.xlsx` app. The user's data arrives intact, every time.

---

## Target Platform

- **v1:** macOS only (Universal binary — Intel + Apple Silicon)
- **Future:** Windows (same core logic, platform-specific UI shell)

## Distribution

- GitHub Releases (`.app` in a `.zip`, built automatically by GitHub Actions)
- Homebrew cask (future)
- `pip install csvsafe` for CLI-only usage (future)

## Build Toolchain

- **Language:** Python 3.11+
- **Packaging:** PyInstaller → macOS `.app` bundle
- **UI framework:** PyObjC (direct `NSStatusBar`, `NSApplication` delegate — no wrapper libraries)
- **Key dependencies:** `pyobjc-framework-Cocoa` (menubar + app events), `openpyxl` (XLSX writing), Python `csv` stdlib (parsing)

---

## Architecture

The application is structured as three decoupled layers: input handlers, a processor, and output handlers. Input handlers own the flow — they read data, call the parser, pass the result to the converter, and hand the workbook to the writer. The processor is stateless and knows nothing about input sources or output destinations.

This separation enables future platform ports (Windows), alternative input methods (watch folder, API), and alternative output formats.

```
┌─────────────────────────────────────────────────────┐
│                 Input Handler                        │
│  (owns the flow: read → parse → convert → write)    │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │   File   │  │Clipboard │  │  (Future:         │  │
│  │  (drop/  │  │  (menu   │  │  watch dir,       │  │
│  │ open-with│  │  click)  │  │  stdin, etc)      │  │
│  └────┬─────┘  └────┬─────┘  └──────┬────────────┘  │
│       │              │               │               │
│       ▼              ▼               ▼               │
│   1. Read raw text                                   │
│   2. Call parser → ParseResult (generator of rows)   │
│   3. Call converter(ParseResult) → Workbook          │
│   4. Call writer(Workbook, InputSource) → open file  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│              Processor (stateless)                    │
│                                                      │
│  parser.py                                           │
│    Input:  raw text (str)                            │
│    Output: ParseResult (row generator, delimiter,    │
│            has_header)                               │
│                                                      │
│  converter.py                                        │
│    Input:  ParseResult                               │
│    Output: openpyxl Workbook                         │
│            (all cells text, header formatting only   │
│             if has_header is True)                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│              Output Handler (stateless)               │
│                                                      │
│  writer.py                                           │
│    Input:  Workbook + InputSource                    │
│    Output: writes .xlsx, sets permissions, opens     │
└──────────────────────────────────────────────────────┘
```

---

## Module Breakdown

### `src/csvsafe/core/parser.py` — CSV Parsing

**Responsibilities:**
- Accept raw text input (string)
- Sniff delimiter using `csv.Sniffer` (sample first N bytes)
- Fall back to comma if `csv.Error` is raised
- Sniff for header row
- Treat `.csv` and `.tsv` identically (format detection is delimiter-based via Python `csv`)
- Return `ParseResult` with a **generator** of rows (not a list), enabling streaming of large files

**Public interface:**
```python
@dataclass
class ParseResult:
    rows: Generator[list[str], None, None]
    delimiter: str
    has_header: bool

def parse_csv(text: str) -> ParseResult
```

**Note:** Because `rows` is a generator, it can only be consumed once. The converter must process it in a single pass, which aligns with `openpyxl`'s `append()` API.

### `src/csvsafe/core/converter.py` — XLSX Conversion

**Responsibilities:**
- Accept a `ParseResult` directly
- Create openpyxl Workbook with all cells formatted as text
- If `has_header` is True: bold header row, freeze top row, enable auto-filters
- If `has_header` is False: no header formatting, no freeze, no filters
- Auto-size column widths (capped at a reasonable max)
- Return Workbook object (does NOT write to disk)

**Public interface:**
```python
def convert_to_workbook(parse_result: ParseResult, sheet_name: str = "Sheet1") -> Workbook
```

### `src/csvsafe/core/writer.py` — Output Handling

**Responsibilities:**
- Determine output path based on source context
- Implement auto-increment naming: `file.xlsx`, `file (1).xlsx`, `file (2).xlsx`
- Write workbook to disk
- Set read-only permission when writing to temp (clipboard source)
- Open file in system default application

**Public interface:**
```python
@dataclass
class InputSource:
    origin: Literal["file", "clipboard"]
    source_path: Optional[Path]  # None for clipboard

def write_and_open(workbook: Workbook, source: InputSource) -> Path
```

**Output path logic:**
- `origin == "file"` → write to same directory as source, name derived from source filename, auto-increment suffix if file exists. File is writable.
- `origin == "clipboard"` → write to system temp directory, name is `CSVSafe_clipboard_<timestamp>.xlsx`, file is read-only (forces Save As in spreadsheet apps).

### `src/csvsafe/input/file_handler.py` — File Input

**Responsibilities:**
- Accept a single file path from macOS open-file events and drag-and-drop (`.csv` and `.tsv`)
- Read file contents with encoding detection (UTF-8, then latin-1 fallback)
- **Owns the flow:** calls parser, passes `ParseResult` to converter, passes workbook to writer
- Constructs `InputSource` with `origin="file"` and the source path

**Public interface:**
```python
def handle_file(path: str) -> None
```

### `src/csvsafe/input/clipboard_handler.py` — Clipboard Input

**Responsibilities:**
- Read clipboard text from `NSPasteboard` (via platform abstraction)
- Validate only that clipboard data is text and non-empty
- Delegate CSV validity to Python `csv` parsing (do not pre-validate delimiter/shape)
- **Owns the flow:** calls parser, passes `ParseResult` to converter, passes workbook to writer
- Constructs `InputSource` with `origin="clipboard"`

**Public interface:**
```python
def handle_clipboard() -> None
```

**Platform note:** This module uses native macOS pasteboard APIs through `platform/macos.py`. A Windows port would swap in `win32clipboard` with the same interface.

### `src/csvsafe/app.py` — macOS Menubar Application

**Responsibilities:**
- Create and manage menubar icon using PyObjC (`NSStatusBar`, `NSStatusItem`)
- Implement `NSApplication` delegate for open-file events (drag-and-drop, Open With) and process one input file per conversion request
- Register menu items:
  - "Convert Clipboard" — calls clipboard handler
  - "About CSVSafe" — opens `https://github.com/jamesshannon/csvsafe/blob/main/MANUAL.md` in default browser
  - "Quit" — terminates app
- Display macOS notifications on success/failure via `UNUserNotificationCenter` (modern API)

**App configuration (Info.plist):**
- `LSUIElement = true` (no dock icon when running, no ⌘Tab presence)
- `CFBundleDocumentTypes` registers `.csv`, `.tsv` as supported file types (listed in Open With, not default)
- Users can set CSVSafe as the default handler manually via Finder → Get Info → Open With → Change All

**PyObjC implementation notes:**
- `NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusBarItemLength)` for the menubar icon
- `NSMenu` with `NSMenuItem` for the dropdown
- `application_openFiles_` delegate method for file open events
- `NSWorkspace.sharedWorkspace().openURL_()` for opening the About page
- `NSWorkspace.sharedWorkspace().openFile_()` for opening XLSX files in the system default app

### `src/csvsafe/cli.py` — Command-Line Interface

A CLI for scripting, automation, and testing the core logic without the menubar app:

```
csvsafe convert input.csv                  # writes input.xlsx alongside source
csvsafe convert input.csv -o output.xlsx   # explicit output path
csvsafe clipboard                          # clipboard → temp xlsx, opens in default app
csvsafe clipboard -o output.xlsx           # clipboard → specific path
```

**Implementation:** Uses `argparse`. Calls the same input handlers, parser, converter, and writer as the GUI app. No additional dependencies.

**v1 scope notes:**
- No batch conversion mode
- Header detection is automatic only (`csv.Sniffer().has_header()`), with no CLI override flag

### `src/csvsafe/platform/macos.py` — macOS Platform Utilities

**Responsibilities:**
- Open file in default application (`NSWorkspace`)
- Open URL in default browser (`NSWorkspace`)
- Show notification (`UNUserNotificationCenter`)
- Read clipboard text via `NSPasteboard` and expose text/non-text state

Isolates all macOS-specific system calls. A future `platform/windows.py` would provide the same interface.

---

## XLSX Formatting Spec

Every cell in the output workbook is formatted as **Text** (`number_format = '@'`). This is the core guarantee of the tool.

**If header row is detected (`has_header == True`):**
- **Header row (row 1):** Bold font
- **Freeze panes:** Top row frozen (always visible when scrolling)
- **Auto-filters:** Enabled on the header row

**If no header row detected (`has_header == False`):**
- No bold, no freeze, no filters

**Always applied:**
- **Column widths:** Auto-sized based on content, capped at 50 characters
- **Sheet name:** Derived from source filename (file input) or "Clipboard" (clipboard input)

No other formatting is applied. The output should feel like a clean, unstyled spreadsheet — not a report.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Clipboard is empty or not text | macOS notification: "No CSV data found on clipboard" |
| File is not readable / doesn't exist | macOS notification with filename |
| CSV sniffing fails | Fall back to comma delimiter, proceed |
| CSV parsing fails entirely | macOS notification: "Could not parse CSV data" |
| Output directory not writable | macOS notification, suggest Save As |
| XLSX file write fails | macOS notification with error detail |
| Non-fatal parsing/conversion issue with recoverable data | Continue conversion, create XLSX, notify user with warning summary |

Fatal errors should fail gracefully with a user-friendly macOS notification. Non-fatal errors should continue when data remains recoverable/usable, produce an XLSX, and surface a warning notification. The app should never crash or show a traceback.

---

## Testing Plan

### Unit Tests (`tests/`)

**`test_parser.py`**
- Comma-delimited input parses correctly
- Tab-delimited input is detected and parsed correctly
- Semicolon-delimited input is detected and parsed correctly
- Mixed quoting styles are handled
- Empty input raises appropriate error
- Binary / non-text input raises appropriate error
- Sniffer failure falls back to comma
- UTF-8 content with special characters is preserved
- Very large rows (100+ columns) parse correctly
- Rows with inconsistent column counts are handled
- Result `rows` is a generator, not a list
- Generator yields `list[str]` for each row
- Header detection works for files with and without headers

**`test_converter.py`**
- All cells in output workbook have text format (`@`)
- When `has_header` is True: header row is bold, freeze panes set, auto-filters enabled
- When `has_header` is False: no bold, no freeze, no filters
- `ParseResult` is consumed correctly (generator input)
- Column widths are reasonable (not 0, not exceeding cap)
- Leading zeros are preserved (e.g., "007" stays "007")
- Long numbers are preserved (e.g., "123456789012345" is not scientific notation)
- Date-like strings are preserved (e.g., "3-5" stays "3-5")
- Empty cells are handled
- Single-row input (header only) works
- Unicode content is preserved

**`test_writer.py`**
- File source: output is written alongside source file
- File source: output filename matches source with `.xlsx` extension
- File source: auto-increment works (`file.xlsx`, `file (1).xlsx`, `file (2).xlsx`)
- File source: output file is writable
- Clipboard source: output is written to temp directory
- Clipboard source: output file is read-only
- Output file can be opened by openpyxl (valid XLSX)

**`test_file_handler.py`**
- Valid CSV file is read and processed
- UTF-8 encoded file is handled
- Latin-1 encoded file is handled (fallback)
- Non-existent file path returns error
- Non-readable file returns error
- Handler calls parser → converter → writer in correct order

**`test_clipboard_handler.py`**
- Valid CSV text from clipboard is processed
- Empty clipboard returns appropriate error
- Non-text clipboard content (e.g., image data) returns appropriate error
- Malformed CSV text that cannot be parsed returns graceful fatal error
- Handler calls parser → converter → writer in correct order

**`test_cli.py`**
- `convert` subcommand with single file works
- `convert` subcommand with explicit `-o` output path works
- `clipboard` subcommand works
- `clipboard` subcommand with `-o` output path works
- Invalid file path prints error and exits with non-zero code
- Missing subcommand prints help

### Integration Tests

- End-to-end: CSV file → XLSX file → verify cell values and formatting in output
- End-to-end: clipboard text → XLSX file → verify cell values and formatting
- Round-trip: known CSV with tricky data (leading zeros, long numbers, date-like strings, unicode) → XLSX → verify every value is preserved exactly
- Large file: 100k+ row CSV processes without excessive memory usage (generator streaming)

### Manual Testing Checklist (pre-release)

- [ ] App launches and shows menubar icon
- [ ] App does not show dock icon or appear in ⌘Tab
- [ ] Drag CSV/TSV onto dock-pinned app icon → converts and opens in default `.xlsx` app
- [ ] Right-click CSV → Open With → CSVSafe → converts and opens
- [ ] Menubar → Convert Clipboard → converts and opens
- [ ] Menubar → About CSVSafe → opens GitHub manual page in browser
- [ ] Clipboard with tab-separated data works
- [ ] Converting same file twice produces `file.xlsx` and `file (1).xlsx`
- [ ] Clipboard output is read-only (spreadsheet app prompts Save As on save)
- [ ] File output is writable (spreadsheet app saves in place)
- [ ] Notification appears on error (empty clipboard, bad file)
- [ ] App survives rapid repeated conversions
- [ ] App works after sleep/wake cycle
- [ ] Universal binary runs on both Intel and Apple Silicon
- [ ] CLI `csvsafe convert` works from terminal
- [ ] CLI `csvsafe clipboard` works from terminal

---

## Project Structure

```
csvsafe/
├── README.md
├── MANUAL.md                # End-user manual (linked from About menu)
├── LICENSE                  # MIT
├── pyproject.toml           # Project metadata, dependencies
├── Makefile                 # build, test, package shortcuts
│
├── src/
│   └── csvsafe/
│       ├── __init__.py
│       ├── app.py               # PyObjC menubar app (macOS entry point)
│       ├── cli.py               # CLI entry point
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── parser.py         # CSV sniffing + parsing → ParseResult (generator)
│       │   ├── converter.py      # ParseResult → openpyxl Workbook
│       │   └── writer.py         # Write XLSX, manage paths, open file
│       │
│       ├── input/
│       │   ├── __init__.py
│       │   ├── file_handler.py   # File read + encoding detection + flow orchestration
│       │   └── clipboard_handler.py  # Clipboard read + flow orchestration
│       │
│       └── platform/
│           ├── __init__.py
│           └── macos.py          # macOS-specific: open file, notifications, clipboard
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_converter.py
│   ├── test_writer.py
│   ├── test_file_handler.py
│   ├── test_clipboard_handler.py
│   ├── test_cli.py
│   └── fixtures/
│       ├── simple.csv
│       ├── tabs.tsv
│       ├── leading_zeros.csv
│       ├── long_numbers.csv
│       ├── date_like.csv
│       ├── unicode.csv
│       └── semicolons.csv
│
├── packaging/
│   ├── csvsafe.spec          # PyInstaller spec file
│   ├── icon.icns             # macOS app icon
│   ├── menubar_icon.png      # Menubar glyph (18x18, monochrome)
│   └── Info.plist.template   # CFBundleDocumentTypes, LSUIElement, etc.
│
├── .github/
│   └── workflows/
│       ├── test.yml           # Run tests on every push / PR
│       └── release.yml        # Build + package + upload on tag push
│
└── docs/
    └── DEVELOPMENT.md
```

---

## CI/CD

### `.github/workflows/test.yml` — Continuous Integration

**Triggers:** Every push to `main`, every pull request.

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies (`pip install -e ".[dev]"`)
4. Run linter (`ruff check`)
5. Run tests (`pytest tests/ -v`)
6. Report results

### `.github/workflows/release.yml` — Build & Release

**Triggers:** Push of a version tag (e.g., `v1.0.0`).

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install dependencies (runtime + build)
4. Run full test suite (gate the release on passing tests)
5. Build macOS `.app` via PyInstaller using `packaging/csvsafe.spec`
6. Create `.zip` of the `.app` bundle: `CSVSafe-<version>-macos.zip`
7. Create GitHub Release from the tag
8. Upload `.zip` as release asset

**Notes:**
- The release workflow must run on `macos-latest` (GitHub Actions runner) since PyInstaller produces platform-specific output
- Universal binary (Intel + Apple Silicon) requires building with `--target-arch universal2` or producing two builds and merging with `lipo`
- v1 is unsigned. macOS Gatekeeper will warn users on first launch; the manual documents bypass (right-click → Open).

---

## Dependencies

### Runtime
- `pyobjc-framework-Cocoa` — macOS menubar, app delegate, workspace, pasteboard
- `pyobjc-framework-UserNotifications` — modern macOS notifications (`UNUserNotificationCenter`)
- `openpyxl` — XLSX file creation
- Python stdlib: `csv`, `tempfile`, `pathlib`, `os`, `stat`, `argparse`

### Development
- `pyinstaller` — App bundling
- `pytest` — Testing
- `ruff` — Linting

### No other dependencies. Keep it minimal.

---

## Build Commands (Makefile)

```makefile
install:        pip install -e ".[dev]"
test:           pytest tests/ -v
lint:           ruff check src/ tests/
build:          pyinstaller packaging/csvsafe.spec
clean:          rm -rf build/ dist/ *.egg-info
```

---

## End-User Manual

A `MANUAL.md` file lives at the repository root and is linked from the app's "About CSVSafe" menu item. It is hosted at:

`https://github.com/jamesshannon/csvsafe/blob/main/MANUAL.md`

### Manual Contents

The manual should cover:

1. **What CSVSafe does** — One-paragraph explanation of the problem and solution.

2. **Installation** — Download `.zip` from GitHub Releases, unzip, drag `CSVSafe.app` to Applications. Note Gatekeeper bypass if unsigned (right-click → Open on first launch).

3. **Converting CSV files**
   - Drag and drop a `.csv` or `.tsv` file onto the CSVSafe app icon (in Finder, on the dock, or on the desktop)
   - Or: right-click a `.csv` or `.tsv` file → Open With → CSVSafe
   - The converted `.xlsx` appears in the same folder as the original and opens automatically in the system default `.xlsx` app

4. **Converting clipboard data**
   - Copy CSV or tab-separated data to clipboard (from a webpage, another app, terminal, etc.)
   - Click the CSVSafe menubar icon → "Convert Clipboard"
   - A temporary `.xlsx` file opens in the default `.xlsx` app. It is read-only — use File → Save As to save permanently.

5. **Adding CSVSafe to your Dock** — Open Finder → Applications → drag CSVSafe to the Dock. You can now drop CSV files directly onto the dock icon.

6. **Setting CSVSafe as the default app for CSV/TSV files** — Right-click any `.csv` or `.tsv` file → Get Info → Open With → select CSVSafe → click "Change All."

7. **Launching CSVSafe at login** — System Settings → General → Login Items → add CSVSafe. The menubar icon will always be available.

8. **Using the command line**
   - `csvsafe convert myfile.csv` — converts and opens
   - `csvsafe convert myfile.csv -o output.xlsx` — converts to specific path
   - `csvsafe clipboard` — converts clipboard and opens
   - `csvsafe clipboard -o output.xlsx` — converts clipboard to specific path

9. **How it works** — All cells are formatted as text in the output XLSX. This prevents Excel from modifying your data. If a header row is detected, it is bolded with filters enabled and the top row is frozen.

10. **Troubleshooting**
    - "CSVSafe can't be opened because it is from an unidentified developer" → Right-click → Open
    - Clipboard conversion shows "No CSV data found" → Ensure you copied text, not an image or file
    - Output file not appearing → Check that the source directory is writable

---

## Future Enhancements (not in v1)

- **Windows support:** Same core modules, replace PyObjC shell with Windows UI system tray APIs and provide a Windows clipboard implementation, package with PyInstaller for Windows `.exe`. Add Windows build to `release.yml`.
- **Smart mode:** Attempt to detect which columns are "real" numbers vs. identifiers, format only identifiers as text
- **Global keyboard shortcut:** (e.g., ⌘⇧V for "safe paste") via PyObjC `CGEvent` tap
- **Watch folder:** Monitor a directory for new CSVs and auto-convert
- **Homebrew cask:** `brew install --cask csvsafe`
- **Configurable defaults:** Preferences for output location, whether to auto-open, header formatting on/off
- **Default handler prompt:** First-launch dialog offering to set CSVSafe as the default app for CSV/TSV files via `LSSetDefaultRoleHandlerForContentType`
