"""Output formatters for EXIF data."""

import json
import csv
from pathlib import Path
from typing import Optional
from io import StringIO

from .core import ExifData
from .utils import Colors, header


class TableFormatter:
    """Format EXIF data as a readable table."""
    
    CATEGORIES = {
        "Camera": ["camera_make", "camera_model", "software", "lens_make", "lens_model"],
        "Date/Time": ["date_time", "date_time_original"],
        "GPS": ["gps_latitude", "gps_longitude", "gps_altitude"],
        "Exposure": ["exposure_time", "f_number", "iso", "focal_length"],
        "Image": ["image_width", "image_height", "orientation", "color_space"],
    }
    
    DISPLAY_NAMES = {
        "camera_make": "Camera Make",
        "camera_model": "Camera Model",
        "software": "Software",
        "lens_make": "Lens Make",
        "lens_model": "Lens Model",
        "date_time": "Date/Time",
        "date_time_original": "Date Taken",
        "gps_latitude": "Latitude",
        "gps_longitude": "Longitude",
        "gps_altitude": "Altitude",
        "exposure_time": "Exposure",
        "f_number": "F-Number",
        "iso": "ISO",
        "focal_length": "Focal Length",
        "image_width": "Width",
        "image_height": "Height",
        "orientation": "Orientation",
        "color_space": "Color Space",
    }
    
    def format(self, exif_data: ExifData, filename: str) -> str:
        """Format EXIF data as a table string."""
        lines = []
        lines.append(f"\n{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        lines.append(f"{Colors.BOLD}  {filename}{Colors.RESET}")
        lines.append(f"{Colors.BOLD}{'─' * 50}{Colors.RESET}")
        
        has_data = False
        for category, fields in self.CATEGORIES.items():
            category_data = []
            for field in fields:
                value = getattr(exif_data, field, None)
                if value is not None:
                    display_name = self.DISPLAY_NAMES.get(field, field)
                    category_data.append((display_name, self._format_value(value)))
            
            if category_data:
                has_data = True
                lines.append(f"\n{Colors.CYAN}{category}{Colors.RESET}")
                lines.append(f"{Colors.CYAN}{'─' * 20}{Colors.RESET}")
                for name, value in category_data:
                    lines.append(f"  {name:<18} {value}")
        
        if not has_data:
            lines.append(f"\n{Colors.YELLOW}No EXIF metadata found{Colors.RESET}")
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_value(self, value) -> str:
        """Format a value for display."""
        if isinstance(value, float):
            if value is not None:
                return f"{value:.6f}" if abs(value) < 100 else f"{value:.2f}"
            return "N/A"
        return str(value)


class JsonFormatter:
    """Format EXIF data as JSON."""
    
    def __init__(self, pretty: bool = True):
        self.pretty = pretty
    
    def format(self, exif_data: ExifData, filename: str) -> str:
        """Format EXIF data as JSON string."""
        data = {
            "filename": filename,
            **exif_data.to_dict()
        }
        
        if self.pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def to_file(self, exif_data: ExifData, filename: str, output_path: Path) -> None:
        """Write EXIF data to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.format(exif_data, filename))


class CsvFormatter:
    """Format EXIF data as CSV."""
    
    def __init__(self):
        self.fieldnames = [
            "filename", "camera_make", "camera_model", "software",
            "date_time", "date_time_original", "gps_latitude", "gps_longitude",
            "gps_altitude", "exposure_time", "f_number", "iso", "focal_length",
            "image_width", "image_height", "orientation", "color_space",
            "lens_make", "lens_model"
        ]
    
    def format(self, exif_data: ExifData, filename: str) -> str:
        """Format EXIF data as CSV row."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.fieldnames)
        
        row_data = {"filename": filename, **exif_data.to_dict()}
        writer.writerow(row_data)
        
        return output.getvalue().rstrip("\n")
    
    def format_header(self) -> str:
        """Return CSV header row."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.fieldnames)
        writer.writeheader()
        return output.getvalue().rstrip("\n")
    
    def to_file(self, exif_data: ExifData, filename: str, output_path: Path, append: bool = False) -> None:
        """Write EXIF data to CSV file."""
        mode = "a" if append else "w"
        write_header = not append or not output_path.exists()
        
        with open(output_path, mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            if write_header:
                writer.writeheader()
            row_data = {"filename": filename, **exif_data.to_dict()}
            writer.writerow(row_data)
    
    @staticmethod
    def from_multiple(data_list: list[tuple[ExifData, str]]) -> str:
        """Create CSV from multiple ExifData entries.
        
        Args:
            data_list: List of (ExifData, filename) tuples
        """
        output = StringIO()
        formatter = CsvFormatter()
        writer = csv.DictWriter(output, fieldnames=formatter.fieldnames)
        writer.writeheader()
        
        for exif_data, filename in data_list:
            row_data = {"filename": filename, **exif_data.to_dict()}
            writer.writerow(row_data)
        
        return output.getvalue()
