"""EXIF CLI - CLI tool for extracting, exporting, and removing EXIF metadata."""

__version__ = "1.0.0"
__author__ = "Jose Audisio"
__license__ = "MIT"

from .core import ExifTool
from .formatters import TableFormatter, JsonFormatter, CsvFormatter

__all__ = ["ExifTool", "TableFormatter", "JsonFormatter", "CsvFormatter"]
