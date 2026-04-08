"""Pytest configuration and fixtures for exiftool-cli tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from exiftool_cli.core import ExifTool, ExifData
from exiftool_cli.formatters import TableFormatter, JsonFormatter, CsvFormatter


@pytest.fixture
def assets_dir():
    """Return the test assets directory."""
    return Path(__file__).parent.parent / "assets" / "test_images"


@pytest.fixture
def jpeg_with_exif(assets_dir):
    """Return path to JPEG with EXIF data."""
    return assets_dir / "jpeg_exif.jpg"


@pytest.fixture
def png_no_exif(assets_dir):
    """Return path to PNG without EXIF data."""
    return assets_dir / "png_exif.png"


@pytest.fixture
def tiff_with_exif(assets_dir):
    """Return path to TIFF with EXIF data."""
    return assets_dir / "tiff_exif.tiff"


@pytest.fixture
def jpeg_no_exif(assets_dir):
    """Return path to JPEG without EXIF data."""
    return assets_dir / "no_exif.jpg"


@pytest.fixture
def exif_tool():
    """Return an ExifTool instance."""
    return ExifTool()


@pytest.fixture
def table_formatter():
    """Return a TableFormatter instance."""
    return TableFormatter()


@pytest.fixture
def json_formatter():
    """Return a JsonFormatter instance."""
    return JsonFormatter()


@pytest.fixture
def csv_formatter():
    """Return a CsvFormatter instance."""
    return CsvFormatter()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Return a temporary output directory."""
    return tmp_path


@pytest.fixture
def sample_exif_data():
    """Return a sample ExifData object for testing."""
    return ExifData(
        raw={},
        camera_make="Canon",
        camera_model="EOS R5",
        software="exiftool-cli test",
        date_time="2024:03:15 10:30:00",
        date_time_original="2024:03:15 10:30:00",
        gps_latitude=40.5,
        gps_longitude=-74.0,
        gps_altitude=100.0,
        exposure_time="1/250",
        f_number=2.8,
        iso=400,
        focal_length=50.0,
        orientation=1,
        image_width=800,
        image_height=600,
        color_space="sRGB",
        lens_make="Canon",
        lens_model="RF 50mm F1.2L USM",
    )
