"""Tests for EXIF removal functionality."""

import pytest
from pathlib import Path

from exiftool_cli.core import ExifTool, ExifError


class TestRemove:
    """Test EXIF removal operations."""
    
    def test_remove_exif_preserves_image(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that removing EXIF preserves the image itself."""
        output_path = temp_output_dir / "clean.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        assert output_path.exists()
        
        from PIL import Image
        with Image.open(output_path) as img:
            assert img.format == "JPEG"
            assert img.size == (800, 600)
    
    def test_remove_exif_removes_all_data(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that removing EXIF actually removes the metadata."""
        output_path = temp_output_dir / "clean.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        extracted = exif_tool.extract(output_path)
        
        assert extracted.camera_make is None
        assert extracted.camera_model is None
        assert extracted.iso is None
        assert extracted.gps_latitude is None
    
    def test_remove_exif_with_keep_gps(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that --keep-gps preserves GPS data."""
        output_path = temp_output_dir / "clean_gps.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=True)
        
        extracted = exif_tool.extract(output_path)
        
        assert extracted.camera_make is None
        assert extracted.camera_model is None
        assert extracted.gps_latitude is not None
        assert extracted.gps_longitude is not None
        assert extracted.gps_latitude == 40.5
    
    def test_remove_nonexistent_file_raises_error(self, exif_tool, tmp_path):
        """Test removing non-existent file raises ExifError."""
        input_path = tmp_path / "nonexistent.jpg"
        output_path = tmp_path / "output.jpg"
        
        with pytest.raises(ExifError, match="Cannot read"):
            exif_tool.remove(input_path, output_path)
    
    def test_remove_creates_output_directory(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_output_dir / "subdir" / "nested"
        output_path = output_dir / "clean.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path)
        
        assert output_path.exists()
    
    def test_remove_preserves_image_quality(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that image quality is preserved when removing EXIF."""
        output_path = temp_output_dir / "clean.jpg"
        
        original_size = jpeg_with_exif.stat().st_size
        exif_tool.remove(jpeg_with_exif, output_path)
        new_size = output_path.stat().st_size
        
        size_diff_percent = abs(new_size - original_size) / original_size * 100
        assert size_diff_percent < 50
    
    def test_remove_tiff_format(self, exif_tool, tiff_with_exif, temp_output_dir):
        """Test removing EXIF from TIFF format."""
        output_path = temp_output_dir / "clean.tiff"
        
        exif_tool.remove(tiff_with_exif, output_path, keep_gps=False)
        
        assert output_path.exists()
        
        extracted = exif_tool.extract(output_path)
        assert extracted.camera_make is None
    
    def test_has_exif_after_remove(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test has_exif returns False after removal."""
        output_path = temp_output_dir / "clean.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        assert exif_tool.has_exif(output_path) is False
    
    def test_has_gps_after_remove_keep_gps(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test GPS remains when keep_gps=True."""
        output_path = temp_output_dir / "clean_gps.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=True)
        
        extracted = exif_tool.extract(output_path)
        assert extracted.gps_latitude is not None
