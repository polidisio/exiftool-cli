"""Tests for EXIF export functionality."""

import json
import csv
from pathlib import Path

import pytest

from exiftool_cli.formatters import JsonFormatter


class TestExport:
    """Test EXIF export to JSON and CSV formats."""
    
    def test_export_to_json_format(self, exif_tool, jpeg_with_exif, json_formatter, temp_output_dir):
        """Test exporting EXIF to JSON format."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        output_path = temp_output_dir / "output.json"
        
        json_formatter.to_file(exif_data, jpeg_with_exif.name, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert data["filename"] == jpeg_with_exif.name
        assert data["camera_make"] == "Canon"
        assert data["camera_model"] == "EOS R5"
    
    def test_export_to_csv_format(self, exif_tool, jpeg_with_exif, csv_formatter, temp_output_dir):
        """Test exporting EXIF to CSV format."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        output_path = temp_output_dir / "output.csv"
        
        csv_formatter.to_file(exif_data, jpeg_with_exif.name, output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]["filename"] == jpeg_with_exif.name
        assert rows[0]["camera_make"] == "Canon"
    
    def test_csv_has_all_columns(self, exif_tool, jpeg_with_exif, csv_formatter, temp_output_dir):
        """Test CSV output has all expected columns."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        output_path = temp_output_dir / "output.csv"
        
        csv_formatter.to_file(exif_data, jpeg_with_exif.name, output_path)
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        expected_columns = [
            "filename", "camera_make", "camera_model", "software",
            "date_time", "date_time_original", "gps_latitude", "gps_longitude",
            "gps_altitude", "exposure_time", "f_number", "iso", "focal_length",
            "image_width", "image_height", "orientation", "color_space",
            "lens_make", "lens_model"
        ]
        
        for col in expected_columns:
            assert col in headers
    
    def test_json_contains_all_tags(self, exif_tool, jpeg_with_exif, json_formatter, temp_output_dir):
        """Test JSON output contains all EXIF tags."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        output_path = temp_output_dir / "output.json"
        
        json_formatter.to_file(exif_data, jpeg_with_exif.name, output_path)
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "filename" in data
        assert "camera_make" in data
        assert "gps_latitude" in data
        assert "gps_longitude" in data
        assert "iso" in data
    
    def test_csv_append_mode(self, exif_tool, jpeg_with_exif, tiff_with_exif, csv_formatter, temp_output_dir):
        """Test appending to existing CSV file."""
        output_path = temp_output_dir / "output.csv"
        
        exif_data1 = exif_tool.extract(jpeg_with_exif)
        csv_formatter.to_file(exif_data1, jpeg_with_exif.name, output_path)
        
        exif_data2 = exif_tool.extract(tiff_with_exif)
        csv_formatter.to_file(exif_data2, tiff_with_exif.name, output_path, append=True)
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["filename"] == jpeg_with_exif.name
        assert rows[1]["filename"] == tiff_with_exif.name
    
    def test_from_multiple(self, exif_tool, jpeg_with_exif, tiff_with_exif, csv_formatter):
        """Test creating CSV from multiple entries."""
        data_list = [
            (exif_tool.extract(jpeg_with_exif), jpeg_with_exif.name),
            (exif_tool.extract(tiff_with_exif), tiff_with_exif.name),
        ]
        
        csv_output = csv_formatter.from_multiple(data_list)
        
        assert "filename" in csv_output
        assert jpeg_with_exif.name in csv_output
        assert tiff_with_exif.name in csv_output
    
    def test_json_pretty_print(self, exif_tool, jpeg_with_exif, json_formatter):
        """Test JSON formatter with pretty printing."""
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        output = json_formatter.format(exif_data, jpeg_with_exif.name)
        
        assert "\n" in output
        assert "  " in output
    
    def test_json_no_pretty_print(self, exif_tool, jpeg_with_exif):
        """Test JSON formatter without pretty printing."""
        formatter = JsonFormatter(pretty=False)
        exif_data = exif_tool.extract(jpeg_with_exif)
        
        output = formatter.format(exif_data, jpeg_with_exif.name)
        
        assert "\n" not in output
