"""Tests for EXIF extraction functionality."""

import pytest
from pathlib import Path

from exiftool_cli.core import ExifTool, ExifData, ExifError


class TestExtract:
    """Test EXIF extraction from various image formats."""
    
    def test_extract_exif_from_jpeg(self, exif_tool, jpeg_with_exif):
        """Test extracting EXIF from JPEG file."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        assert exif_data is not None
        assert isinstance(exif_data, ExifData)
        assert exif_data.camera_make == "Canon"
        assert exif_data.camera_model == "EOS R5"
        assert exif_data.iso == 400
        assert exif_data.focal_length == 50.0
    
    def test_extract_exif_from_tiff(self, exif_tool, tiff_with_exif):
        """Test extracting EXIF from TIFF file (may or may not have EXIF)."""
        exif_data = exif_tool.extract(tiff_with_exif)
        
        assert exif_data is not None
        assert isinstance(exif_data, ExifData)
    
    def test_extract_exif_from_png(self, exif_tool, png_no_exif):
        """Test extracting from PNG (limited EXIF support)."""
        exif_data = exif_tool.extract(png_no_exif)
        
        assert exif_data is not None
        assert isinstance(exif_data, ExifData)
    
    def test_no_exif_returns_empty_dict(self, exif_tool, jpeg_no_exif):
        """Test extracting from image without EXIF returns minimal data."""
        exif_data = exif_tool.extract(jpeg_no_exif)
        
        assert exif_data is not None
        assert exif_data.camera_make is None
        assert exif_data.camera_model is None
        assert exif_data.gps_latitude is None
    
    def test_has_exif_jpeg(self, exif_tool, jpeg_with_exif):
        """Test has_exif returns True for JPEG with EXIF."""
        assert exif_tool.has_exif(jpeg_with_exif) is True
    
    def test_has_exif_no_exif(self, exif_tool, jpeg_no_exif):
        """Test has_exif returns False for image without EXIF."""
        assert exif_tool.has_exif(jpeg_no_exif) is False
    
    def test_extract_nonexistent_file_raises_error(self, exif_tool, tmp_path):
        """Test extracting from non-existent file raises ExifError."""
        fake_path = tmp_path / "nonexistent.jpg"
        
        with pytest.raises(ExifError, match="Cannot read"):
            exif_tool.extract(fake_path)
    
    def test_get_all_tags(self, exif_tool, jpeg_with_exif):
        """Test getting all raw EXIF tags."""
        tags = exif_tool.get_all_tags(jpeg_with_exif)
        
        assert isinstance(tags, dict)
        assert len(tags) > 0
    
    def test_gps_data_extraction(self, exif_tool, jpeg_with_exif):
        """Test GPS coordinates are properly extracted and converted."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        assert exif_data.gps_latitude is not None
        assert exif_data.gps_longitude is not None
        assert exif_data.gps_altitude is not None
        assert exif_data.gps_latitude == 40.5
        assert exif_data.gps_longitude == -74.0
    
    def test_exposure_data_extraction(self, exif_tool, jpeg_with_exif):
        """Test exposure settings are properly extracted."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        assert exif_data.exposure_time is not None
        assert "1/250" in exif_data.exposure_time
        assert exif_data.f_number == 2.8
        assert exif_data.iso == 400


class TestExifData:
    """Test ExifData class functionality."""
    
    def test_from_piexif_with_data(self):
        """Test creating ExifData from piexif format."""
        exif_dict = {
            "0th": {
                0x010F: b"Canon",
                0x0110: b"EOS R5",
            },
            "Exif": {
                0x829A: (1, 250),
                0x829D: (28, 10),
                0x8827: 400,
                0x920A: (50, 1),
                0xA001: 1,
            },
            "GPS": {},
            "1st": {},
        }
        
        exif_data = ExifData.from_piexif(exif_dict)
        
        assert exif_data.camera_make == "Canon"
        assert exif_data.camera_model == "EOS R5"
        assert exif_data.iso == 400
    
    def test_from_piexif_empty(self):
        """Test creating ExifData from empty dict."""
        exif_data = ExifData.from_piexif({})
        
        assert exif_data.raw == {}
        assert exif_data.camera_make is None
    
    def test_to_dict(self, sample_exif_data):
        """Test converting ExifData to dictionary."""
        result = sample_exif_data.to_dict()
        
        assert isinstance(result, dict)
        assert result["camera_make"] == "Canon"
        assert result["camera_model"] == "EOS R5"
        assert "raw" not in result
