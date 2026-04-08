# exiftool-cli(1) exiftool-cli User Manual
# exiftool-cli(1)

## NAME

exiftool-cli - CLI tool for extracting, exporting, and removing EXIF metadata from photos

## SYNOPSIS

**exiftool-cli** [--version] [--help] <command> [<args>]

## DESCRIPTION

exiftool-cli is a command-line tool for working with EXIF metadata in images. It supports extracting, exporting, and removing EXIF data from JPEG, PNG, and TIFF images.

## COMMANDS

### extract

Display EXIF metadata in a table format.

```bash
exiftool-cli extract <photo>
```

### export

Export EXIF metadata to JSON or CSV file.

```bash
exiftool-cli export <photo> -o <output>
```

Options:
- **-o, --output**: Output file path (.json or .csv required)

### remove

Remove EXIF metadata from image.

```bash
exiftool-cli remove <photo> -o <output>
```

Options:
- **-o, --output**: Output file path (required)
- **--keep-gps**: Keep GPS data while removing other EXIF

### batch

Batch process multiple images in a folder.

```bash
exiftool-cli batch --folder <path> [options]
```

Options:
- **--folder, -f**: Folder containing images (required)
- **--output, -o**: Output folder (default: same as input)
- **--recursive, -r**: Process subfolders recursively
- **--extract**: Extract and display EXIF metadata
- **--export**: Export format (json or csv)
- **--remove**: Remove EXIF metadata
- **--keep-gps**: Keep GPS data when removing (use with --remove)

### interactive

Launch interactive menu mode.

```bash
exiftool-cli interactive
```

## EXIT STATUS

- **0**: Success
- **1**: Error (file not found, invalid format, etc.)

## EXAMPLES

Extract EXIF from a photo:

```bash
$ exiftool-cli extract photo.jpg
```

Export to JSON:

```bash
$ exiftool-cli export photo.jpg -o metadata.json
```

Export to CSV:

```bash
$ exiftool-cli export photo.jpg -o metadata.csv
```

Remove all EXIF:

```bash
$ exiftool-cli remove photo.jpg -o clean.jpg
```

Remove EXIF but keep GPS:

```bash
$ exiftool-cli remove photo.jpg --keep-gps -o clean.jpg
```

Batch extract:

```bash
$ exiftool-cli batch --folder ./photos --extract
```

Batch remove with recursive:

```bash
$ exiftool-cli batch --folder ./photos --recursive --remove
```

## SUPPORTED FORMATS

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tif, .tiff)

## FILES

~/.config/exiftool-cli/ - Configuration directory (future use)

## SEE ALSO

- piexif(1) - Python EXIF library
- exiftool(1) - Perl EXIF tool

## VERSION

1.0.0

## AUTHOR

Jose Audisio <jmaudisio@users.noreply.github.com>

## LICENSE

MIT License
