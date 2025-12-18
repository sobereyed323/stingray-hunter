"""
AI-powered analysis and recommendations for tower hunting.
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .tower_db import TowerDatabase, TowerRecord
from .gps import GPSCoordinate


@dataclass
class ScanRecommendation:
    """Recommended scan location with reasoning."""
    location: GPSCoordinate
    reason: str
    priority: int  # 1 = highest
    distance_from_center: float


@dataclass
class HuntingPlan:
    """Complete hunting plan for a suspicious tower."""
    target_tower: TowerRecord
    threat_level: str  # "HIGH", "MEDIUM", "LOW"
    estimated_location: Optional[GPSCoordinate]
    scan_points: List[ScanRecommendation]
    analysis: str
    next_steps: List[str]


class AIAnalyzer:
    """AI-powered analysis for optimal tower hunting."""
    
    def __init__(self, db: TowerDatabase):
        self.db = db
    
    def identify_top_threat(self) -> Optional[TowerRecord]:
        """
        Identify the most suspicious tower that needs investigation.
        
        Returns the highest priority target based on:
        - Signal strength anomalies
        - Newness (recently appeared)
        - Suspicious flag
        - Frequency band (5G more concerning for IMSI catchers)
        """
        suspicious = self.db.get_suspicious_towers()
        
        if not suspicious:
            # No explicitly suspicious towers, look for new strong signals
            all_towers = self.db.get_all_towers()
            
            # Score towers by suspicion factors
            scored = []
            for tower in all_towers:
                score = 0
                
                # Very strong signal (closer than expected)
                if tower.avg_signal > -30:
                    score += 50
                
                # New tower (not baseline)
                if not tower.is_baseline:
                    score += 30
                
                # 5G towers (more sophisticated tech)
                if tower.technology == "5G":
                    score += 20
                
                # Few sightings (appeared recently)
                if tower.times_seen < 3:
                    score += 15
                
                scored.append((score, tower))
            
            if scored:
                scored.sort(reverse=True, key=lambda x: x[0])
                return scored[0][1]
            
            return None
        
        # Return most suspicious with strongest signal
        return max(suspicious, key=lambda t: t.avg_signal)
    
    def create_hunting_plan(
        self, 
        tower: TowerRecord,
        user_location: Optional[GPSCoordinate] = None
    ) -> HuntingPlan:
        """
        Create an intelligent hunting plan for a tower.
        
        Args:
            tower: Target tower to locate
            user_location: User's current GPS position (optional)
        
        Returns:
            Complete HuntingPlan with scan points and analysis
        """
        
        # Determine threat level
        threat_level = self._assess_threat_level(tower)
        
        # Estimate rough location if we have measurements
        estimated_location = None
        measurements = self.db.get_location_measurements(tower.unique_id)
        
        if measurements and len(measurements) > 0:
            # Average of existing measurements as rough estimate
            avg_lat = sum(m['latitude'] for m in measurements) / len(measurements)
            avg_lng = sum(m['longitude'] for m in measurements) / len(measurements)
            estimated_location = GPSCoordinate(avg_lat, avg_lng)
        
        # Generate optimal scan points
        scan_points = self._generate_scan_points(
            tower, 
            estimated_location or user_location,
            measurements
        )
        
        # Generate analysis
        analysis = self._generate_analysis(tower, measurements)
        
        # Generate next steps
        next_steps = self._generate_next_steps(tower, len(measurements))
        
        return HuntingPlan(
            target_tower=tower,
            threat_level=threat_level,
            estimated_location=estimated_location,
            scan_points=scan_points,
            analysis=analysis,
            next_steps=next_steps
        )
    
    def _assess_threat_level(self, tower: TowerRecord) -> str:
        """Assess threat level of a tower."""
        score = 0
        
        # Very strong signal (suspiciously close)
        if tower.avg_signal > -25:
            score += 3
        elif tower.avg_signal > -35:
            score += 2
        
        # Explicitly marked suspicious
        if tower.is_suspicious:
            score += 3
        
        # New tower
        if not tower.is_baseline and tower.times_seen < 5:
            score += 2
        
        # 5G (more sophisticated)
        if tower.technology == "5G":
            score += 1
        
        if score >= 6:
            return "HIGH"
        elif score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_scan_points(
        self,
        tower: TowerRecord,
        center: Optional[GPSCoordinate],
        existing_measurements: List[Dict]
    ) -> List[ScanRecommendation]:
        """Generate optimal scan point locations."""
        
        if center is None:
            # No location data, can't suggest specific points
            return [
                ScanRecommendation(
                    location=GPSCoordinate(0, 0),  # Placeholder
                    reason="Need initial scan location - use your current position",
                    priority=1,
                    distance_from_center=0
                )
            ]
        
        # Estimate appropriate distance based on signal strength
        # Stronger signal = tower is closer = smaller scan radius
        if tower.avg_signal > -30:
            radius_m = 100  # Very close
        elif tower.avg_signal > -45:
            radius_m = 200  # Medium distance
        else:
            radius_m = 300  # Farther away
        
        # Convert radius to degrees (rough approximation)
        radius_deg = radius_m / 111000  # ~111km per degree latitude
        
        # Generate 3 points in optimal triangle pattern
        # Points at 0°, 120°, 240° around center
        angles = [0, 120, 240]
        points = []
        
        for i, angle_deg in enumerate(angles):
            angle_rad = math.radians(angle_deg)
            
            # Calculate offset
            dlat = radius_deg * math.cos(angle_rad)
            dlon = radius_deg * math.sin(angle_rad) / math.cos(math.radians(center.latitude))
            
            location = GPSCoordinate(
                center.latitude + dlat,
                center.longitude + dlon
            )
            
            # Check if we already have a measurement near this point
            has_nearby = any(
                abs(m['latitude'] - location.latitude) < 0.0005 and
                abs(m['longitude'] - location.longitude) < 0.0005
                for m in existing_measurements
            )
            
            reason = f"Point {i+1}: {radius_m}m {'north' if angle_deg == 0 else 'southwest' if angle_deg == 120 else 'southeast'}"
            if has_nearby:
                reason += " (already scanned nearby)"
            
            points.append(ScanRecommendation(
                location=location,
                reason=reason,
                priority=i + 1,
                distance_from_center=radius_m
            ))
        
        return points
    
    def _generate_analysis(self, tower: TowerRecord, measurements: List[Dict]) -> str:
        """Generate human-readable analysis."""
        lines = []
        
        # Signal analysis
        lines.append(f"Signal: {tower.avg_signal:.1f} dBm average")
        if tower.avg_signal > -30:
            lines.append("⚠️ VERY STRONG - Tower is extremely close or using excessive power")
        elif tower.avg_signal > -45:
            lines.append("📡 Strong signal - Tower within a few hundred meters")
        
        # Technology
        lines.append(f"Technology: {tower.technology}")
        if tower.technology == "5G":
            lines.append("⚠️ 5G towers can be used for advanced tracking")
        
        # Measurement status
        if measurements:
            lines.append(f"Measurements: {len(measurements)} location(s) scanned")
            if len(measurements) >= 3:
                lines.append("✓ Sufficient data for triangulation")
            else:
                lines.append(f"⚠️ Need {3 - len(measurements)} more scan(s) for accurate location")
        
        # Threat assessment
        if tower.is_suspicious:
            lines.append("🚨 Flagged as SUSPICIOUS by anomaly detector")
        
        if not tower.is_baseline and tower.times_seen < 5:
            lines.append("⚠️ New/rare tower - not in your baseline")
        
        return "\n".join(lines)
    
    def _generate_next_steps(self, tower: TowerRecord, measurement_count: int) -> List[str]:
        """Generate actionable next steps."""
        steps = []
        
        if measurement_count == 0:
            steps.append("1. Go to recommended Point 1")
            steps.append("2. Run: scan-locate --lat X --lon Y")
            steps.append("3. Drive to Point 2 and repeat")
        elif measurement_count < 3:
            steps.append(f"1. Go to Point {measurement_count + 1} (see recommendations)")
            steps.append("2. Run scan-locate with those coordinates")
            steps.append(f"3. Complete {3 - measurement_count} more scan(s)")
        else:
            steps.append("1. Run: triangulate " + tower.unique_id)
            steps.append("2. Review estimated location on Google Maps")
            steps.append("3. Investigate the physical location")
            steps.append("4. Report to authorities if  confirmed rogue")
        
        return steps
    
    def analyze_triangulation_quality(
        self,
        measurements: List[Dict]
    ) -> Dict[str, any]:
        """
        Analyze the quality of triangulation data.
        
        Returns:
            Quality metrics and recommendations
        """
        if len(measurements) < 3:
            return {
                'quality': 'INSUFFICIENT',
                'confidence': 0,
                'recommendation': f'Need {3 - len(measurements)} more measurements'
            }
        
        # Check geometric distribution
        lats = [m['latitude'] for m in measurements]
        lons = [m['longitude'] for m in measurements]
        
        # Calculate spread
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        
        avg_spread = (lat_range + lon_range) / 2
        
        # Good spread is ~0.001 degrees (100m)
        if avg_spread < 0.0005:
            quality = 'POOR'
            confidence = 30
            recommendation = 'Scan points too close together - move farther apart'
        elif avg_spread < 0.002:
            quality = 'GOOD'
            confidence = 70
            recommendation = 'Good triangulation setup'
        else:
            quality = 'EXCELLENT'
            confidence = 90
            recommendation = 'Excellent triangulation geometry'
        
        return {
            'quality': quality,
            'confidence': confidence,
            'recommendation': recommendation,
            'spread_meters': avg_spread * 111000
        }
