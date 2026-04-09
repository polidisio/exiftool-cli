"""Utility functions for exiftool_cli."""

import os
import sys
import click
from pathlib import Path
from typing import Optional

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    _has_colorama = True
except ImportError:
    _has_colorama = False

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
SUPPORTED_MIMETYPES = {"image/jpeg", "image/png", "image/tiff"}


class Colors:
    """Terminal color codes."""
    if _has_colorama:
        GREEN = Fore.GREEN
        RED = Fore.RED
        YELLOW = Fore.YELLOW
        BLUE = Fore.BLUE
        CYAN = Fore.CYAN
        MAGENTA = Fore.MAGENTA
        BOLD = Style.BRIGHT
        RESET = Style.RESET_ALL
        DIM = Style.DIM
    else:
        GREEN = RED = YELLOW = BLUE = CYAN = MAGENTA = BOLD = RESET = DIM = ""


def success(msg: str) -> None:
    """Print success message in green."""
    click.echo(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def error(msg: str) -> None:
    """Print error message in red."""
    click.echo(f"{Colors.RED}✗ {msg}{Colors.RESET}", err=True)


def warning(msg: str) -> None:
    """Print warning message in yellow."""
    click.echo(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def info(msg: str) -> None:
    """Print info message in blue."""
    click.echo(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def header(msg: str) -> None:
    """Print header message in bold."""
    click.echo(f"{Colors.BOLD}{msg}{Colors.RESET}")


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    return click.confirm(f"{Colors.CYAN}{prompt}{Colors.RESET}", default=default)


def validate_file(path: Path) -> tuple[bool, Optional[str]]:
    """Validate that file exists and is a supported image type.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"File not found: {path}"
    
    if not path.is_file():
        return False, f"Not a file: {path}"
    
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported format '{suffix}'. Use: {', '.join(SUPPORTED_EXTENSIONS)}"
    
    return True, None


def validate_folder(path: Path) -> tuple[bool, Optional[str]]:
    """Validate that folder exists.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Folder not found: {path}"
    
    if not path.is_dir():
        return False, f"Not a directory: {path}"
    
    return True, None


def get_image_files(folder: Path, recursive: bool = False) -> list[Path]:
    """Get all supported image files in folder.
    
    Args:
        folder: Path to folder
        recursive: Whether to search subdirectories
    
    Returns:
        List of Path objects for supported images
    """
    files = []
    pattern = "**/*" if recursive else "*"
    
    for item in folder.glob(pattern):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(item)
    
    return sorted(files)


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_file_size_diff_str(original_path: Path, new_path: Path) -> str:
    """Get formatted size difference between two files."""
    if not original_path.exists() or not new_path.exists():
        return ""
    
    original_size = original_path.stat().st_size
    new_size = new_path.stat().st_size
    diff = new_size - original_size
    sign = "+" if diff > 0 else ""
    
    return f"{format_size(original_size)} → {format_size(new_size)} ({sign}{format_size(diff)})"


class ProgressTracker:
    """Simple progress tracker for batch operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current += increment
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        bar_len = 30
        filled = int(bar_len * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        click.echo(f"\r{self.description}: [{bar}] {self.current}/{self.total} ({percent:.0f}%)", nl=False)
    
    def finish(self) -> None:
        """Finish progress tracking."""
        click.echo()


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if needed."""
    path.mkdir(parents=True, exist_ok=True)


def get_output_path(input_path: Path, output_dir: Optional[Path] = None, suffix: str = "") -> Path:
    """Generate output path based on input path.
    
    Args:
        input_path: Original file path
        output_dir: Optional output directory (defaults to input's directory)
        suffix: Optional suffix to add before extension
    
    Returns:
        Output Path object
    """
    if output_dir:
        ensure_directory(output_dir)
        return output_dir / f"{input_path.stem}{suffix}{input_path.suffix}"
    return input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"


def is_exif_supported_format(path: Path) -> bool:
    """Check if file format supports EXIF metadata."""
    suffix = path.suffix.lower()
    return suffix in {".jpg", ".jpeg", ".tif", ".tiff"}
