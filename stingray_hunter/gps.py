"""
GPS coordinate handling and validation.
"""

import re
from dataclasses import dataclass
from typing import Tuple, Optional
import math


@dataclass
class GPSCoordinate:
    """Represents a GPS coordinate (latitude, longitude)."""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate coordinates."""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
    
    def distance_to(self, other: 'GPSCoordinate') -> float:
        """
        Calculate distance to another coordinate using Haversine formula.
        Returns distance in meters.
        """
        # Earth radius in meters
        R = 6371000
        
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def __str__(self):
        return f"{self.latitude:.6f},{self.longitude:.6f}"
    
    @classmethod
    def parse(cls, coord_str: str) -> 'GPSCoordinate':
        """
        Parse GPS coordinates from string.
        Accepts formats:
        - "37.7749,-122.4194"
        - "37.7749, -122.4194"
        - "37°46'29.64\"N, 122°25'9.84\"W" (DMS format)
        """
        coord_str = coord_str.strip()
        
        # Try decimal format first (most common)
        decimal_pattern = r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)'
        match = re.match(decimal_pattern, coord_str)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
            return cls(lat, lon)
        
        # Try DMS format
        dms_pattern = r'(\d+)°(\d+)\'([\d.]+)"([NS])\s*,?\s*(\d+)°(\d+)\'([\d.]+)"([EW])'
        match = re.match(dms_pattern, coord_str)
        if match:
            lat_d, lat_m, lat_s, lat_dir = match.groups()[:4]
            lon_d, lon_m, lon_s, lon_dir = match.groups()[4:]
            
            lat = float(lat_d) + float(lat_m)/60 + float(lat_s)/3600
            if lat_dir == 'S':
                lat = -lat
                
            lon = float(lon_d) + float(lon_m)/60 + float(lon_s)/3600
            if lon_dir == 'W':
                lon = -lon
                
            return cls(lat, lon)
        
        raise ValueError(f"Invalid GPS coordinate format: {coord_str}")


def google_maps_url(coord: GPSCoordinate) -> str:
    """Generate Google Maps URL for a coordinate."""
    return f"https://maps.google.com/?q={coord.latitude},{coord.longitude}"
