# imgmeta

Personal CLI tool for extracting, exporting, and removing EXIF metadata from photos.

> **Note:** This tool uses [Piexif](https://github.com/hMatoba/Piexif) internally — it is not related to the Perl-based [exiftool](https://exiftool.org/). The name reflects its functionality, not the underlying library.

## Features

- **Interactive Mode**: Menu-driven interface with native macOS file explorer
- **Extract EXIF**: Display metadata in a readable table format
- **Export**: Save metadata to JSON or CSV files
- **Remove**: Strip EXIF data while preserving image quality
- **Batch Process**: Handle entire folders with progress display
- **Native File Picker**: Uses macOS file/folder dialogs

## Installation

### macOS (Homebrew) - Recommended

```bash
brew install polidisio/tap/imgmeta
```

### pip / uv

```bash
uv tool install imgmeta
```

### From Source

```bash
git clone https://github.com/polidisio/exiftool-cli.git
cd imgmeta
uv tool install -e .
```

## Usage

### Interactive Mode (Recommended)

Simply run `imgmeta` without arguments to launch the interactive menu:

```bash
imgmeta
```

You'll see:

```
╔══════════════════════════════════════════╗
║        EXIFTOOL-CLI v1.0.0              ║
╚══════════════════════════════════════════╝

Main Menu
────────────────────────────────────────
  Selected: None

  [1] Select photos (file explorer)
  [2] Show EXIF preview
  [3] Export EXIF
  [4] Remove EXIF
  [0] Exit

Select option:
```

**Flow:**
1. Press `1` to open the macOS file explorer and select photos
2. Press `2` to preview EXIF data
3. Press `3` to export (choose JSON or CSV, use file explorer for output folder)
4. Press `4` to remove EXIF (optionally use file explorer for output folder)
5. Press `0` to exit

### Command Line Mode

#### Extract EXIF

```bash
imgmeta extract photo.jpg
```

Output:
```
──────────────────────────────────────────────────
  photo.jpg
──────────────────────────────────────────────────

Camera
────────────────────
  Camera Make        Canon
  Camera Model       EOS R5
  Software           Digital Photo Professional

Date/Time
────────────────────
  Date/Time         2024:03:15 10:30:00
  Date Taken        2024:03:15 10:30:00

GPS
────────────────────
  Latitude           40.500000
  Longitude          -74.000000
  Altitude           100.0

Exposure
────────────────────
  Exposure           1/250
  F-Number           2.8
  ISO                400
  Focal Length       50.0
```

#### Export to JSON

```bash
imgmeta export photo.jpg -o output.json
```

#### Export to CSV

```bash
imgmeta export photo.jpg -o output.csv
```

#### Remove EXIF

```bash
imgmeta remove photo.jpg -o clean_photo.jpg
```

#### Remove EXIF but keep GPS

```bash
imgmeta remove photo.jpg --keep-gps -o clean_photo.jpg
```

#### Batch Process

```bash
# Extract EXIF from all photos in a folder
imgmeta batch --folder /path/to/photos --extract

# Remove EXIF from all photos
imgmeta batch --folder /path/to/photos --remove

# Export metadata to CSV
imgmeta batch --folder /path/to/photos --export csv -o metadata.csv

# Process recursively
imgmeta batch --folder /path/to/photos --recursive --remove
```

## Command Line Options

| Command | Option | Description |
|---------|--------|-------------|
| (interactive) | - | Launches interactive menu mode |
| extract | `<file>` | Image file to extract EXIF from |
| export | `-o, --output` | Output file path (.json or .csv) |
| remove | `-o, --output` | Output file path |
| remove | `--keep-gps` | Preserve GPS data only |
| batch | `--folder, -f` | Folder containing images |
| batch | `--recursive, -r` | Process subfolders |
| batch | `--extract` | Extract EXIF display |
| batch | `--export` | Export format (json/csv) |
| batch | `--remove` | Remove EXIF metadata |

## Supported Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tif, .tiff)

## Development

```bash
# Clone the repository
git clone https://github.com/polidisio/exiftool-cli.git
cd imgmeta

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/exiftool_cli --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Jose Audisio
