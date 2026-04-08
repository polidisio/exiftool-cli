"""Core EXIF manipulation functionality."""

import io
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from PIL import Image

try:
    import piexif
    _has_piexif = True
except ImportError:
    _has_piexif = False

from .utils import error as utils_error, warning as utils_warning, is_exif_supported_format


EXIF_TAG_NAMES = {
    0x010F: "Camera Make",
    0x0110: "Camera Model",
    0x0131: "Software",
    0x0132: "DateTime",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x8769: "ExifIFD",
    0x8825: "GPS IFD",
    0x829A: "ExposureTime",
    0x829D: "FNumber",
    0x8827: "ISOSpeedRatings",
    0x920A: "FocalLength",
    0xA001: "ColorSpace",
    0xA002: "ImageWidth",
    0xA003: "ImageHeight",
    0x0112: "Orientation",
    0x9000: "ExifVersion",
    0xA430: "OwnerName",
    0xA431: "SerialNumber",
    0xA432: "LensInfo",
    0xA433: "LensMake",
    0xA434: "LensModel",
    0xA435: "LensSerialNumber",
}

GPS_TAG_NAMES = {
    0x0000: "GPSVersionID",
    0x0001: "GPSLatitudeRef",
    0x0002: "GPSLatitude",
    0x0003: "GPSLongitudeRef",
    0x0004: "GPSLongitude",
    0x0005: "GPSAltitudeRef",
    0x0006: "GPSAltitude",
    0x0007: "GPSTimeStamp",
    0x001D: "GPSDateStamp",
}


@dataclass
class ExifData:
    """Container for EXIF data with human-readable access."""
    raw: dict
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    date_time: Optional[str] = None
    date_time_original: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    exposure_time: Optional[str] = None
    f_number: Optional[float] = None
    iso: Optional[int] = None
    focal_length: Optional[float] = None
    orientation: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    color_space: Optional[str] = None
    lens_make: Optional[str] = None
    lens_model: Optional[str] = None
    
    @classmethod
    def from_piexif(cls, exif_dict: dict) -> "ExifData":
        """Create ExifData from piexif format dict."""
        if not exif_dict:
            return cls(raw={})
        
        camera = {}
        gps = {}
        exif_ifd = {}
        
        if "0th" in exif_dict:
            camera = exif_dict["0th"]
        if "Exif" in exif_dict:
            exif_ifd = exif_dict["Exif"]
        if "GPS" in exif_dict:
            gps = exif_dict["GPS"]
        
        def get_str(tag_dict: dict, tag: int) -> Optional[str]:
            val = tag_dict.get(tag)
            if val is None:
                return None
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace")
            return str(val)
        
        def get_int(tag_dict: dict, tag: int) -> Optional[int]:
            val = tag_dict.get(tag)
            if val is None:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        
        def get_float(tag_dict: dict, tag: int) -> Optional[float]:
            val = tag_dict.get(tag)
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        
        def dms_to_decimal(dms: tuple) -> Optional[float]:
            if not dms or len(dms) != 3:
                return None
            try:
                degrees = float(dms[0][0]) / float(dms[0][1])
                minutes = float(dms[1][0]) / float(dms[1][1])
                seconds = float(dms[2][0]) / float(dms[2][1])
                return degrees + minutes / 60 + seconds / 3600
            except (ValueError, TypeError, ZeroDivisionError):
                return None
        
        lat = None
        lat_ref = gps.get(0x0001)
        if 0x0002 in gps:
            lat = dms_to_decimal(gps[0x0002])
            if lat and lat_ref == b"S":
                lat = -lat
        
        lon = None
        lon_ref = gps.get(0x0003)
        if 0x0004 in gps:
            lon = dms_to_decimal(gps[0x0004])
            if lon and lon_ref == b"W":
                lon = -lon
        
        alt = None
        if 0x0006 in gps:
            try:
                alt = float(gps[0x0006][0]) / float(gps[0x0006][1])
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        exposure = None
        if 0x829A in exif_ifd:
            try:
                val = exif_ifd[0x829A]
                if isinstance(val, tuple):
                    val = float(val[0]) / float(val[1])
                exposure = f"1/{int(1/val)}" if 0 < val < 1 else f"{val}s"
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        fnum = None
        if 0x829D in exif_ifd:
            try:
                val = exif_ifd[0x829D]
                if isinstance(val, tuple):
                    fnum = float(val[0]) / float(val[1])
                else:
                    fnum = float(val)
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        focal = None
        if 0x920A in exif_ifd:
            try:
                val = exif_ifd[0x920A]
                if isinstance(val, tuple):
                    focal = float(val[0]) / float(val[1])
                else:
                    focal = float(val)
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        color_map = {1: "sRGB", 65535: "Uncalibrated"}
        color = color_map.get(exif_ifd.get(0xA001))
        
        return cls(
            raw=exif_dict,
            camera_make=get_str(camera, 0x010F),
            camera_model=get_str(camera, 0x0110),
            software=get_str(camera, 0x0131),
            date_time=get_str(camera, 0x0132),
            date_time_original=get_str(exif_ifd, 0x9003),
            gps_latitude=lat,
            gps_longitude=lon,
            gps_altitude=alt,
            exposure_time=exposure,
            f_number=fnum,
            iso=get_int(exif_ifd, 0x8827),
            focal_length=focal,
            orientation=get_int(camera, 0x0112),
            image_width=get_int(exif_ifd, 0xA002),
            image_height=get_int(exif_ifd, 0xA003),
            color_space=color,
            lens_make=get_str(exif_ifd, 0xA433),
            lens_model=get_str(exif_ifd, 0xA434),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        result = {}
        for key, value in self.__dict__.items():
            if key != "raw" and value is not None:
                result[key] = value
        return result


class ExifError(Exception):
    """Custom exception for EXIF operations."""
    pass


class ExifTool:
    """Main class for EXIF operations."""
    
    def __init__(self):
        if not _has_piexif:
            raise ExifError("piexif library is required. Install with: pip install piexif")
    
    def extract(self, image_path: Path) -> ExifData:
        """Extract EXIF data from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            ExifData object with extracted data
            
        Raises:
            ExifError: If file cannot be read or is corrupted
        """
        try:
            if is_exif_supported_format(image_path):
                exif_dict = piexif.load(str(image_path))
            else:
                exif_dict = {}
        except Exception as e:
            raise ExifError(f"Cannot read EXIF from {image_path.name}: {e}")
        
        return ExifData.from_piexif(exif_dict)
    
    def has_exif(self, image_path: Path) -> bool:
        """Check if image has EXIF data."""
        try:
            if is_exif_supported_format(image_path):
                exif_dict = piexif.load(str(image_path))
                return bool(exif_dict and (exif_dict.get("0th") or exif_dict.get("Exif") or exif_dict.get("GPS")))
            return False
        except Exception:
            return False
    
    def remove(self, image_path: Path, output_path: Path, keep_gps: bool = False) -> None:
        """Remove EXIF metadata from image.
        
        Args:
            image_path: Path to input image
            output_path: Path to output image
            keep_gps: If True, preserve GPS data only
            
        Raises:
            ExifError: If file cannot be processed
        """
        try:
            if is_exif_supported_format(image_path):
                exif_dict = piexif.load(str(image_path))
            else:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        except Exception as e:
            raise ExifError(f"Cannot read {image_path.name}: {e}")
        
        if keep_gps:
            gps_data = exif_dict.get("GPS", {})
            exif_dict = {"0th": {}, "Exif": {}, "GPS": gps_data, "1st": {}, "thumbnail": None}
        else:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        try:
            exif_bytes = piexif.dump(exif_dict)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with Image.open(image_path) as img:
                if img.format == "JPEG":
                    img.save(output_path, "JPEG", exif=exif_bytes, quality=95)
                elif img.format == "TIFF":
                    img.save(output_path, "TIFF", exif=exif_bytes)
                elif img.format == "PNG":
                    img.save(output_path, "PNG", exif=exif_bytes)
                else:
                    img.save(output_path)
        except Exception as e:
            raise ExifError(f"Cannot save {output_path.name}: {e}")
    
    def get_all_tags(self, image_path: Path) -> dict:
        """Get all EXIF tags as raw dictionary.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with all EXIF tags
        """
        try:
            if is_exif_supported_format(image_path):
                exif_dict = piexif.load(str(image_path))
            else:
                return {}
        except Exception:
            return {}
        
        result = {}
        
        for ifd_name, ifd_data in exif_dict.items():
            if ifd_data and isinstance(ifd_data, dict):
                for tag_id, value in ifd_data.items():
                    tag_name = EXIF_TAG_NAMES.get(tag_id, f"Unknown_{tag_id}")
                    if ifd_name == "GPS":
                        tag_name = GPS_TAG_NAMES.get(tag_id, f"Unknown_{tag_id}")
                    result[f"{ifd_name}.{tag_name}"] = self._format_tag_value(value)
        
        return result
    
    def _format_tag_value(self, value) -> str:
        """Format tag value for display."""
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return str(value)
        elif isinstance(value, tuple):
            try:
                if len(value) == 3 and all(isinstance(v, tuple) for v in value):
                    return f"{value[0][0]}/{value[0][1]}, {value[1][0]}/{value[1][1]}, {value[2][0]}/{value[2][1]}"
                return str(value)
            except Exception:
                return str(value)
        return str(value)
