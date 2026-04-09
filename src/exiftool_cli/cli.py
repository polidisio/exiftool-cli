"""CLI commands for exiftool-cli."""

import sys
import csv
from pathlib import Path

import click

from .core import ExifTool, ExifError
from .formatters import TableFormatter, JsonFormatter, CsvFormatter
from .utils import (
    success, error, warning, info, header,
    validate_file, validate_folder, get_image_files,
    format_size, get_file_size_diff_str, ProgressTracker,
    ensure_directory, get_output_path, SUPPORTED_EXTENSIONS
)
from .interactive import InteractiveMode


@click.group()
@click.version_option(version="1.0.0", prog_name="exiftool-cli")
def main():
    """EXIF metadata CLI tool - Extract, export, and remove EXIF data from images."""
    InteractiveMode().run()


@main.command()
@click.argument("photo", type=click.Path(exists=True))
def extract(photo):
    """Extract and display EXIF metadata in table format."""
    photo_path = Path(photo)
    
    is_valid, err_msg = validate_file(photo_path)
    if not is_valid:
        error(err_msg)
        sys.exit(1)
    
    try:
        exif_tool = ExifTool()
        exif_data = exif_tool.extract(photo_path)
        
        formatter = TableFormatter()
        output = formatter.format(exif_data, photo_path.name)
        click.echo(output)
        
    except ExifError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.argument("photo", type=click.Path(exists=True))
@click.option("-o", "--output", "output_path", required=True, type=click.Path(),
              help="Output file path (.json or .csv)")
def export(photo, output_path):
    """Export EXIF metadata to JSON or CSV file."""
    photo_path = Path(photo)
    out_path = Path(output_path)
    
    is_valid, err_msg = validate_file(photo_path)
    if not is_valid:
        error(err_msg)
        sys.exit(1)
    
    ext = out_path.suffix.lower()
    if ext not in {".json", ".csv"}:
        error(f"Unsupported output format '{ext}'. Use .json or .csv")
        sys.exit(1)
    
    try:
        exif_tool = ExifTool()
        exif_data = exif_tool.extract(photo_path)
        
        if ext == ".json":
            formatter = JsonFormatter()
            formatter.to_file(exif_data, photo_path.name, out_path)
        else:
            formatter = CsvFormatter()
            formatter.to_file(exif_data, photo_path.name, out_path)
        
        success(f"Exported to {out_path}")
        
    except ExifError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Export failed: {e}")
        sys.exit(1)


@main.command()
@click.argument("photo", type=click.Path(exists=True))
@click.option("-o", "--output", "output_path", required=True, type=click.Path(),
              help="Output file path")
@click.option("--keep-gps", is_flag=True,
              help="Keep GPS data while removing other EXIF")
def remove(photo, output_path, keep_gps):
    """Remove EXIF metadata from image."""
    photo_path = Path(photo)
    out_path = Path(output_path)
    
    is_valid, err_msg = validate_file(photo_path)
    if not is_valid:
        error(err_msg)
        sys.exit(1)
    
    ensure_directory(out_path.parent)
    
    try:
        exif_tool = ExifTool()
        exif_tool.remove(photo_path, out_path, keep_gps=keep_gps)
        
        size_info = get_file_size_diff_str(photo_path, out_path)
        success(f"Removed EXIF from {photo_path.name} → {out_path.name}")
        if size_info:
            info(f"Size: {size_info}")
        
        if keep_gps:
            info("GPS data preserved")
        
    except ExifError as e:
        error(str(e))
        sys.exit(1)
    except Exception as e:
        error(f"Remove failed: {e}")
        sys.exit(1)


@main.command()
@click.option("--folder", "-f", required=True, type=click.Path(exists=True),
              help="Folder containing images to process")
@click.option("--output", "-o", "output_dir", type=click.Path(),
              help="Output folder (default: same as input)")
@click.option("--remove", is_flag=True,
              help="Remove EXIF metadata")
@click.option("--extract", is_flag=True,
              help="Extract EXIF metadata")
@click.option("--export", "export_format", type=click.Choice(["json", "csv"]),
              help="Export EXIF to file")
@click.option("--recursive", "-r", is_flag=True,
              help="Process subfolders recursively")
@click.option("--keep-gps", is_flag=True,
              help="Keep GPS data when removing (use with --remove)")
def batch(folder, output_dir, remove, extract, export_format, recursive, keep_gps):
    """Batch process multiple images in a folder."""
    folder_path = Path(folder)
    out_dir = Path(output_dir) if output_dir else None
    
    is_valid, err_msg = validate_folder(folder_path)
    if not is_valid:
        error(err_msg)
        sys.exit(1)
    
    if out_dir:
        ensure_directory(out_dir)
    
    if not any([remove, extract, export_format]):
        error("Specify at least one operation: --remove, --extract, or --export")
        sys.exit(1)
    
    files = get_image_files(folder_path, recursive)
    
    if not files:
        warning(f"No supported images found in {folder_path}")
        sys.exit(0)
    
    header(f"Processing {len(files)} files...")
    
    exif_tool = ExifTool()
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    progress = ProgressTracker(len(files), "Processing")
    
    export_data = []
    
    for file_path in files:
        progress.update()
        
        try:
            if remove:
                out_path = get_output_path(file_path, out_dir, "_clean")
                exif_tool.remove(file_path, out_path, keep_gps=keep_gps)
            
            if extract:
                exif_data = exif_tool.extract(file_path)
                formatter = TableFormatter()
                click.echo(formatter.format(exif_data, file_path.name))
            
            if export_format:
                exif_data = exif_tool.extract(file_path)
                export_data.append((exif_data, file_path.name))
            
            results["success"] += 1
            
        except ExifError as e:
            warning(f"Skipped {file_path.name}: {e}")
            results["skipped"] += 1
        except Exception as e:
            error(f"Error processing {file_path.name}: {e}")
            results["failed"] += 1
    
    progress.finish()
    
    if export_format and export_data:
        export_path = out_dir or folder_path
        export_file = export_path / f"exif_export.{export_format}"
        
        if export_format == "json":
            with open(export_file, "w", encoding="utf-8") as f:
                import json
                data = [{"filename": name, **data.to_dict()} for data, name in export_data]
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            with open(export_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "filename", "camera_make", "camera_model", "software",
                    "date_time", "date_time_original", "gps_latitude", "gps_longitude",
                    "gps_altitude", "exposure_time", "f_number", "iso", "focal_length",
                    "image_width", "image_height", "orientation", "color_space",
                    "lens_make", "lens_model"
                ])
                writer.writeheader()
                for exif_data, filename in export_data:
                    writer.writerow({"filename": filename, **exif_data.to_dict()})
        
        success(f"Exported to {export_file}")
    
    info(f"Completed: {results['success']} success, {results['skipped']} skipped, {results['failed']} failed")


@main.command()
def interactive():
    """Launch interactive menu mode."""
    try:
        mode = InteractiveMode()
        mode.run()
    except KeyboardInterrupt:
        click.echo("\nExiting interactive mode.")
    except Exception as e:
        error(f"Interactive mode error: {e}")
        sys.exit(1)


def main_wrapper():
    """Wrapper for entry point."""
    main()


if __name__ == "__main__":
    main_wrapper()
