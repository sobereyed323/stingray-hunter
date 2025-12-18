"""
Cell tower triangulation using signal strength measurements.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional
from .gps import GPSCoordinate


@dataclass
class Measurement:
    """A signal strength measurement at a specific location."""
    location: GPSCoordinate
    signal_dbm: float
    tower_id: str
    timestamp: str


class Triangulator:
    """Triangulate tower location using signal strength measurements."""
    
    def __init__(self, path_loss_exponent: float = 3.0):
        """
        Initialize triangulator.
        
        Args:
            path_loss_exponent: Signal propagation exponent (2-4)
                2.0 = free space
                3.0 = urban environment (default)
                4.0 = dense urban/indoors
        """
        self.path_loss_exponent = path_loss_exponent
    
    def estimate_distance(self, signal_dbm: float, reference_power: float = -40.0) -> float:
        """
        Estimate distance from signal strength using path loss model.
        
        Args:
            signal_dbm: Measured signal strength in dBm
            reference_power: Expected power at 1 meter (default -40 dBm)
        
        Returns:
            Estimated distance in meters
        """
        # Path loss formula: RSSI = A - 10*n*log10(d)
        # Solving for d: d = 10^((A - RSSI) / (10*n))
        
        distance = 10 ** ((reference_power - signal_dbm) / (10 * self.path_loss_exponent))
        return max(distance, 1.0)  # Minimum 1 meter
    
    def trilaterate(self, measurements: List[Measurement]) -> Optional[Tuple[GPSCoordinate, float]]:
        """
        Trilaterate tower position from signal measurements.
        
        Args:
            measurements: List of at least 3 measurements from different locations
        
        Returns:
            Tuple of (estimated_location, accuracy_meters) or None if insufficient data
        """
        if len(measurements) < 3:
            return None
        
        # Estimate distances from each measurement point
        points = []
        for m in measurements:
            distance = self.estimate_distance(m.signal_dbm)
            points.append((m.location, distance))
        
        # Use least squares trilateration
        # This is a simplified 2D approach
        
        # Convert to Cartesian coordinates (approximate for small areas)
        def lat_lon_to_meters(coord: GPSCoordinate) -> Tuple[float, float]:
            # Rough conversion: 1 degree lat ≈ 111km, 1 degree lon varies by latitude
            lat_m = coord.latitude * 111000
            lon_m = coord.longitude * 111000 * math.cos(math.radians(coord.latitude))
            return lat_m, lon_m
        
        def meters_to_lat_lon(x: float, y: float, ref_lat: float) -> GPSCoordinate:
            lat = x / 111000
            lon = y / (111000 * math.cos(math.radians(ref_lat)))
            return GPSCoordinate(lat, lon)
        
        # Use first measurement as reference
        ref_coord = measurements[0].location
        
        # Convert all points to local Cartesian system
        cartesian_points = []
        for location, distance in points:
            x, y = lat_lon_to_meters(location)
            cartesian_points.append((x, y, distance))
        
        # Weighted centroid approach (simple but effective)
        # Weight by inverse distance squared
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for x, y, distance in cartesian_points:
            weight = 1.0 / (distance ** 2)
            weighted_x += x * weight
            weighted_y += y * weight
            total_weight += weight
        
        estimated_x = weighted_x / total_weight
        estimated_y = weighted_y / total_weight
        
        # Convert back to lat/lon
        estimated_location = meters_to_lat_lon(estimated_x, estimated_y, ref_coord.latitude)
        
        # Calculate accuracy estimate (standard deviation of distances)
        distances_to_estimate = [
            estimated_location.distance_to(loc) for loc, _ in points
        ]
        accuracy = sum(distances_to_estimate) / len(distances_to_estimate)
        
        return estimated_location, accuracy
    
    def analyze_measurements(self, measurements: List[Measurement]) -> dict:
        """
        Analyze measurements and provide detailed diagnostics.
        
        Returns dict with:
        - measurement_count
        - avg_signal
        - signal_range
        - locations (as strings)
        """
        if not measurements:
            return {}
        
        signals = [m.signal_dbm for m in measurements]
        
        return {
            'measurement_count': len(measurements),
            'avg_signal': sum(signals) / len(signals),
            'min_signal': min(signals),
            'max_signal': max(signals),
            'signal_range': max(signals) - min(signals),
            'locations': [str(m.location) for m in measurements],
            'estimated_distances': [
                self.estimate_distance(m.signal_dbm) for m in measurements
            ]
        }
