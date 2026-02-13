# CSVSafe Manual

## What CSVSafe does
CSVSafe converts CSV/TSV data into XLSX files where all cells are text-formatted, preventing spreadsheet software from silently changing values.

## Installation
1. Download `CSVSafe-<version>-macos.zip` from GitHub Releases.
2. Unzip and drag `CSVSafe.app` to Applications.
3. On first launch (unsigned app), right-click and choose **Open**.

## Convert CSV/TSV files
- Drag a `.csv` or `.tsv` file onto the app icon.
- Or right-click a file, choose **Open With**, then `CSVSafe`.
- CSVSafe writes `<name>.xlsx` beside the source and opens it.

## Convert clipboard data
- Copy CSV/TSV text.
- Click the CSVSafe menu bar icon and select **Convert Clipboard**.
- CSVSafe opens a read-only temp `.xlsx`; use **Save As** to keep it.

## Dock
Drag CSVSafe from Applications to Dock to enable drop conversion.

## Default app for CSV/TSV
Use Finder **Get Info** on `.csv`/`.tsv` and set **Open With** to CSVSafe.

## Launch at login
System Settings -> General -> Login Items -> add CSVSafe.

## CLI
```bash
csvsafe convert myfile.csv
csvsafe convert myfile.csv -o output.xlsx
csvsafe clipboard
csvsafe clipboard -o output.xlsx
```

## Troubleshooting
- "Unidentified developer": right-click app -> **Open**.
- "No CSV data found": ensure clipboard contains text.
- Output missing: confirm source directory is writable.
