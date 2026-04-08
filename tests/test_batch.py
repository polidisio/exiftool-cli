"""Tests for batch processing functionality."""

import csv
import json
from pathlib import Path

import pytest


class TestBatch:
    """Test batch processing operations."""
    
    def test_batch_process_multiple_formats(self, exif_tool, assets_dir, temp_output_dir):
        """Test batch processing images of different formats."""
        files = list(assets_dir.glob("*"))
        jpeg_files = [f for f in files if f.suffix.lower() in {".jpg", ".jpeg"}]
        
        assert len(jpeg_files) > 0
        
        results = []
        for file_path in jpeg_files:
            exif_data = exif_tool.extract(file_path)
            results.append((exif_data, file_path.name))
        
        assert len(results) == len(jpeg_files)
    
    def test_batch_extract_all_files(self, exif_tool, assets_dir):
        """Test extracting EXIF from all test images."""
        files = list(assets_dir.glob("*"))
        image_files = [f for f in files if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff"}]
        
        for file_path in image_files:
            exif_data = exif_tool.extract(file_path)
            assert exif_data is not None
    
    def test_batch_export_json(self, exif_tool, assets_dir, temp_output_dir):
        """Test batch exporting to JSON."""
        files = list(assets_dir.glob("*.jpg"))
        output_path = temp_output_dir / "batch_export.json"
        
        data_list = []
        for file_path in files:
            exif_data = exif_tool.extract(file_path)
            data_list.append({"filename": file_path.name, **exif_data.to_dict()})
        
        with open(output_path, "w") as f:
            json.dump(data_list, f, indent=2)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert len(data) == len(files)
    
    def test_batch_export_csv(self, exif_tool, assets_dir, temp_output_dir):
        """Test batch exporting to CSV."""
        files = list(assets_dir.glob("*.jpg"))
        output_path = temp_output_dir / "batch_export.csv"
        
        fieldnames = [
            "filename", "camera_make", "camera_model", "software",
            "date_time", "date_time_original", "gps_latitude", "gps_longitude",
            "gps_altitude", "exposure_time", "f_number", "iso", "focal_length",
            "image_width", "image_height", "orientation", "color_space",
            "lens_make", "lens_model"
        ]
        
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for file_path in files:
                exif_data = exif_tool.extract(file_path)
                row = {"filename": file_path.name, **exif_data.to_dict()}
                writer.writerow(row)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == len(files)
    
    def test_batch_remove_all(self, exif_tool, assets_dir, temp_output_dir):
        """Test batch removing EXIF from multiple files."""
        files = list(assets_dir.glob("*.jpg"))
        
        for file_path in files:
            output_path = temp_output_dir / f"{file_path.stem}_clean{file_path.suffix}"
            exif_tool.remove(file_path, output_path, keep_gps=False)
            
            assert output_path.exists()
            
            extracted = exif_tool.extract(output_path)
            assert extracted.camera_make is None
            assert extracted.camera_model is None
    
    def test_batch_remove_keep_gps_multiple(self, exif_tool, assets_dir, temp_output_dir):
        """Test batch removing EXIF while keeping GPS."""
        files = list(assets_dir.glob("*.jpg"))
        
        for file_path in files:
            output_path = temp_output_dir / f"{file_path.stem}_gps{file_path.suffix}"
            exif_tool.remove(file_path, output_path, keep_gps=True)
            
            assert output_path.exists()
            
            original = exif_tool.extract(file_path)
            cleaned = exif_tool.extract(output_path)
            
            if original.gps_latitude is not None:
                assert cleaned.gps_latitude == original.gps_latitude
                assert cleaned.gps_longitude == original.gps_longitude


class TestBatchProgress:
    """Test batch progress tracking."""
    
    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initializes correctly."""
        from exiftool_cli.utils import ProgressTracker
        
        tracker = ProgressTracker(10, "Test")
        
        assert tracker.total == 10
        assert tracker.current == 0
    
    def test_progress_tracker_update(self):
        """Test ProgressTracker update method."""
        from exiftool_cli.utils import ProgressTracker
        
        tracker = ProgressTracker(10, "Test")
        tracker.update(1)
        
        assert tracker.current == 1
        
        tracker.update(3)
        assert tracker.current == 4
