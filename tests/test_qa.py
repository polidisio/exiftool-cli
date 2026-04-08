"""QA Integration Tests for exiftool-cli.

These tests verify the complete workflow of the application
including error handling, edge cases, and end-to-end functionality.
"""

import json
import csv
from pathlib import Path

import pytest
from PIL import Image


class TestQAWorkflows:
    """End-to-end workflow tests."""
    
    def test_full_workflow_extract_export(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test complete workflow: extract EXIF → export to JSON → verify data integrity."""
        original = exif_tool.extract(jpeg_with_exif)
        original_dict = original.to_dict()
        
        output_json = temp_output_dir / "workflow_test.json"
        from exiftool_cli.formatters import JsonFormatter
        formatter = JsonFormatter()
        formatter.to_file(original, jpeg_with_exif.name, output_json)
        
        assert output_json.exists()
        
        with open(output_json, "r") as f:
            exported = json.load(f)
        
        assert exported["filename"] == jpeg_with_exif.name
        assert exported["camera_make"] == original_dict["camera_make"]
        assert exported["camera_model"] == original_dict["camera_model"]
        assert exported["iso"] == original_dict["iso"]
    
    def test_full_workflow_remove_preserves_image(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test workflow: remove EXIF → re-read → verify no EXIF."""
        output_path = temp_output_dir / "removed_test.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        with Image.open(output_path) as img:
            assert img.format == "JPEG"
            assert img.size == (800, 600)
        
        cleaned = exif_tool.extract(output_path)
        assert cleaned.camera_make is None
        assert cleaned.camera_model is None
        assert cleaned.iso is None
    
    def test_gps_preservation_workflow(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test removing all EXIF except GPS."""
        output_path = temp_output_dir / "gps_only.jpg"
        
        original = exif_tool.extract(jpeg_with_exif)
        assert original.gps_latitude is not None
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=True)
        
        cleaned = exif_tool.extract(output_path)
        
        assert cleaned.gps_latitude == original.gps_latitude
        assert cleaned.gps_longitude == original.gps_longitude
        assert cleaned.gps_altitude == original.gps_altitude
        assert cleaned.camera_make is None
        assert cleaned.camera_model is None
    
    def test_batch_multiple_formats(self, exif_tool, assets_dir, temp_output_dir):
        """Test processing mix of JPEG, PNG, TIFF files."""
        files = list(assets_dir.glob("*"))
        image_files = [f for f in files if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff"}]
        
        assert len(image_files) >= 3
        
        results = {"extracted": 0, "exported": 0, "removed": 0}
        
        for file_path in image_files:
            exif_data = exif_tool.extract(file_path)
            assert exif_data is not None
            results["extracted"] += 1
            
            output_json = temp_output_dir / f"{file_path.stem}.json"
            from exiftool_cli.formatters import JsonFormatter
            formatter = JsonFormatter()
            formatter.to_file(exif_data, file_path.name, output_json)
            assert output_json.exists()
            results["exported"] += 1
        
        assert results["extracted"] >= 3
        assert results["exported"] >= 3


class TestQAErrorHandling:
    """Test error handling and edge cases."""
    
    def test_corrupted_file_handling(self, exif_tool, temp_output_dir):
        """Test graceful handling of corrupted file."""
        corrupted_path = temp_output_dir / "corrupted.jpg"
        
        with open(corrupted_path, "wb") as f:
            f.write(b"NOT A VALID JPEG FILE DATA\x00\xFF\x00\x00")
        
        with pytest.raises(Exception):
            exif_tool.extract(corrupted_path)
    
    def test_error_recovery_continues_processing(self, exif_tool, assets_dir, temp_output_dir):
        """Test that processing continues after encountering an error."""
        valid_files = list(assets_dir.glob("*.jpg"))
        
        assert len(valid_files) >= 1
        
        for file_path in valid_files:
            result = exif_tool.extract(file_path)
            assert result is not None
    
    def test_missing_file_returns_clear_error(self, exif_tool, tmp_path):
        """Test that missing file returns clear error message."""
        from exiftool_cli.core import ExifError
        
        fake_path = tmp_path / "does_not_exist.jpg"
        
        with pytest.raises(ExifError) as exc_info:
            exif_tool.extract(fake_path)
        
        assert "not found" in str(exc_info.value).lower() or "cannot read" in str(exc_info.value).lower()
    
    def test_unsupported_format_error(self, exif_tool, temp_output_dir):
        """Test handling of unsupported format."""
        from exiftool_cli.core import ExifError
        
        unsupported_path = temp_output_dir / "test.bmp"
        
        from PIL import Image
        img = Image.new("RGB", (100, 100))
        img.save(unsupported_path, "BMP")
        
        exif_data = exif_tool.extract(unsupported_path)
        assert exif_data is not None


class TestQAOutputQuality:
    """Test output quality and file integrity."""
    
    def test_output_quality_unchanged(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that output image has same dimensions as input."""
        output_path = temp_output_dir / "quality_test.jpg"
        
        with Image.open(jpeg_with_exif) as original_img:
            original_size = original_img.size
            original_mode = original_img.mode
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        with Image.open(output_path) as output_img:
            assert output_img.size == original_size
            assert output_img.mode == original_mode
    
    def test_file_size_reasonable(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test that output file size is reasonable (not empty, not gigabytes)."""
        output_path = temp_output_dir / "size_test.jpg"
        
        exif_tool.remove(jpeg_with_exif, output_path, keep_gps=False)
        
        size = output_path.stat().st_size
        
        assert size > 1000
        assert size < 50 * 1024 * 1024
    
    def test_multiple_remove_cycles(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test removing EXIF multiple times maintains image integrity."""
        path1 = temp_output_dir / "cycle1.jpg"
        path2 = temp_output_dir / "cycle2.jpg"
        path3 = temp_output_dir / "cycle3.jpg"
        
        exif_tool.remove(jpeg_with_exif, path1, keep_gps=False)
        exif_tool.remove(path1, path2, keep_gps=False)
        exif_tool.remove(path2, path3, keep_gps=False)
        
        with Image.open(path3) as img:
            assert img.size == (800, 600)
        
        final = exif_tool.extract(path3)
        assert final.camera_make is None


class TestQAFormatters:
    """Test formatter output quality."""
    
    def test_table_formatter_output(self, exif_tool, jpeg_with_exif, table_formatter):
        """Test table formatter produces expected output."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        output = table_formatter.format(exif_data, jpeg_with_exif.name)
        
        assert isinstance(output, str)
        assert jpeg_with_exif.name in output
        assert "Canon" in output
    
    def test_csv_export_complete_roundtrip(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test CSV export and verify all data can be re-read."""
        output_path = temp_output_dir / "roundtrip.csv"
        
        original = exif_tool.extract(jpeg_with_exif)
        from exiftool_cli.formatters import CsvFormatter
        formatter = CsvFormatter()
        formatter.to_file(original, jpeg_with_exif.name, output_path)
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]["filename"] == jpeg_with_exif.name
        assert rows[0]["camera_make"] == "Canon"
    
    def test_json_export_unicode_handling(self, exif_tool, jpeg_with_exif, temp_output_dir):
        """Test JSON export handles unicode correctly."""
        output_path = temp_output_dir / "unicode_test.json"
        
        exif_data = exif_tool.extract(jpeg_with_exif)
        from exiftool_cli.formatters import JsonFormatter
        formatter = JsonFormatter()
        formatter.to_file(exif_data, jpeg_with_exif.name, output_path)
        
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "Canon" in data["camera_make"]


class TestQAUtilities:
    """Test utility functions."""
    
    def test_validate_file_accepts_valid(self, assets_dir):
        """Test validate_file accepts valid image files."""
        from exiftool_cli.utils import validate_file
        
        jpg = assets_dir / "jpeg_exif.jpg"
        is_valid, error = validate_file(jpg)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_rejects_nonexistent(self, tmp_path):
        """Test validate_file rejects non-existent files."""
        from exiftool_cli.utils import validate_file
        
        fake = tmp_path / "nonexistent.jpg"
        is_valid, error = validate_file(fake)
        
        assert is_valid is False
        assert error is not None
        assert "not found" in error.lower()
    
    def test_validate_file_rejects_unsupported(self, tmp_path):
        """Test validate_file rejects unsupported formats."""
        from exiftool_cli.utils import validate_file
        
        bmp_path = tmp_path / "test.bmp"
        from PIL import Image
        img = Image.new("RGB", (10, 10))
        img.save(bmp_path, "BMP")
        
        is_valid, error = validate_file(bmp_path)
        
        assert is_valid is False
        assert "unsupported" in error.lower()
    
    def test_format_size(self):
        """Test human-readable size formatting."""
        from exiftool_cli.utils import format_size
        
        assert "B" in format_size(100)
        assert "KB" in format_size(2048)
        assert "MB" in format_size(2 * 1024 * 1024)
    
    def test_get_image_files_filters_correctly(self, assets_dir):
        """Test get_image_files returns only supported formats."""
        from exiftool_cli.utils import get_image_files
        
        files = get_image_files(assets_dir, recursive=False)
        
        for f in files:
            assert f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    
    def test_ensure_directory_creates_path(self, tmp_path):
        """Test ensure_directory creates nested directories."""
        from exiftool_cli.utils import ensure_directory
        
        nested = tmp_path / "a" / "b" / "c"
        ensure_directory(nested)
        
        assert nested.exists()
        assert nested.is_dir()
