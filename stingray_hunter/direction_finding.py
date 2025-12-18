"""
Direction Finding (DF) using dual HackRF receivers.
Calculate bearing to signal source using phase difference analysis.
"""

import numpy as np
import math
from typing import Tuple, Optional
from dataclasses import dataclass


# Physical constants
SPEED_OF_LIGHT = 299792458  # meters per second


@dataclass
class DFResult:
    """Direction finding result."""
    bearing_degrees: float
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    signal_strength_dbm: float
    frequency_hz: float
    phase_difference_rad: float
    ambiguity_warning: bool  # True if 180° ambiguity exists


class DirectionFinder:
    """Calculate bearing to signal source using dual receivers."""
    
    def __init__(self, antenna_spacing_m: float = 0.18, calibration_offset_deg: float = 0.0):
        """
        Initialize direction finder.
        
        Args:
            antenna_spacing_m: Physical spacing between antennas in meters
                              Recommended: 0.5λ (half wavelength)
                              GSM 850: 0.18m, LTE 1900: 0.08m, 5G 2500: 0.06m
            calibration_offset_deg: Calibration offset from known bearings
        """
        self.antenna_spacing_m = antenna_spacing_m
        self.calibration_offset_deg = calibration_offset_deg
    
    def calculate_bearing(
        self,
        iq_samples_1: np.ndarray,
        iq_samples_2: np.ndarray,
        frequency_hz: float,
        signal_strength_dbm: float
    ) -> DFResult:
        """
        Calculate bearing from dual receiver IQ samples.
        
        Args:
            iq_samples_1: Complex IQ samples from receiver 1
            iq_samples_2: Complex IQ samples from receiver 2
            frequency_hz: Frequency being monitored
            signal_strength_dbm: Signal strength (for confidence assessment)
        
        Returns:
            DFResult with bearing and metadata
        """
        # Calculate phase difference between receivers
        phase_diff = self._calculate_phase_difference(iq_samples_1, iq_samples_2)
        
        # Convert phase difference to bearing
        bearing = self._phase_to_bearing(phase_diff, frequency_hz)
        
        # Apply calibration offset
        bearing += self.calibration_offset_deg
        
        # Normalize to 0-360°
        bearing = bearing % 360
        
        # Assess confidence
        confidence = self._assess_confidence(signal_strength_dbm, iq_samples_1, iq_samples_2)
        
        # Check for ambiguity (linear array has 180° ambiguity)
        ambiguity = True  # Always true for linear array
        
        return DFResult(
            bearing_degrees=bearing,
            confidence=confidence,
            signal_strength_dbm=signal_strength_dbm,
            frequency_hz=frequency_hz,
            phase_difference_rad=phase_diff,
            ambiguity_warning=ambiguity
        )
    
    def _calculate_phase_difference(
        self,
        signal1: np.ndarray,
        signal2: np.ndarray
    ) -> float:
        """
        Calculate phase difference between two signals using cross-correlation.
        
        Args:
            signal1: Complex IQ samples from antenna 1
            signal2: Complex IQ samples from antenna 2
        
        Returns:
            Phase difference in radians
        """
        # Ensure signals are same length
        min_len = min(len(signal1), len(signal2))
        signal1 = signal1[:min_len]
        signal2 = signal2[:min_len]
        
        # Cross-correlation to find phase offset
        correlation = np.correlate(signal1, np.conj(signal2), mode='full')
        
        # Find peak of correlation
        peak_index = np.argmax(np.abs(correlation))
        
        # Extract phase at peak
        phase_diff = np.angle(correlation[peak_index])
        
        return phase_diff
    
    def _phase_to_bearing(self, phase_diff_rad: float, frequency_hz: float) -> float:
        """
        Convert phase difference to bearing angle.
        
        Args:
            phase_diff_rad: Phase difference in radians
            frequency_hz: Signal frequency
        
        Returns:
            Bearing angle in degrees (0-360°, relative to antenna baseline)
        """
        # Calculate wavelength
        wavelength = SPEED_OF_LIGHT / frequency_hz
        
        # Calculate sin(θ) from phase difference
        # Formula: sin(θ) = (Δφ × λ) / (2π × d)
        k = (phase_diff_rad * wavelength) / (2 * math.pi * self.antenna_spacing_m)
        
        # Clamp to valid range [-1, 1] to avoid math domain errors
        k = max(-1.0, min(1.0, k))
        
        # Calculate angle
        bearing_rad = math.asin(k)
        bearing_deg = math.degrees(bearing_rad)
        
        # Convert from [-90, 90] to [0, 360]
        # Positive angle = signal from right side
        # Negative angle = signal from left side
        if bearing_deg >= 0:
            bearing_deg = 90 - bearing_deg  # 0° = straight ahead
        else:
            bearing_deg = 90 + abs(bearing_deg)
        
        return bearing_deg
    
    def _assess_confidence(
        self,
        signal_strength_dbm: float,
        signal1: np.ndarray,
        signal2: np.ndarray
    ) -> str:
        """
        Assess confidence in bearing measurement.
        
        Args:
            signal_strength_dbm: Signal strength
            signal1: IQ samples from receiver 1
            signal2: IQ samples from receiver 2
        
        Returns:
            Confidence level: "HIGH", "MEDIUM", or "LOW"
        """
        score = 0
        
        # Strong signal = better measurement
        if signal_strength_dbm > -30:
            score += 3
        elif signal_strength_dbm > -45:
            score += 2
        elif signal_strength_dbm > -60:
            score += 1
        
        # Check signal coherence (similar power levels)
        power1 = np.mean(np.abs(signal1) ** 2)
        power2 = np.mean(np.abs(signal2) ** 2)
        
        if power1 > 0 and power2 > 0:
            power_ratio = max(power1, power2) / min(power1, power2)
            if power_ratio < 1.5:  # Within 1.5x
                score += 2
            elif power_ratio < 3:  # Within 3x
                score += 1
        
        # Determine confidence
        if score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def calibrate(self, measured_bearing: float, actual_bearing: float) -> float:
        """
        Calibrate system using a known signal source.
        
        Args:
            measured_bearing: Bearing measured by system
            actual_bearing: Actual bearing to known source
        
        Returns:
            Calibration offset to apply
        """
        offset = actual_bearing - measured_bearing
        
        # Normalize to [-180, 180]
        while offset > 180:
            offset -= 360
        while offset < -180:
            offset += 360
        
        self.calibration_offset_deg = offset
        return offset
    
    def optimal_antenna_spacing(self, frequency_hz: float) -> float:
        """
        Calculate optimal antenna spacing for a frequency.
        
        Args:
            frequency_hz: Operating frequency
        
        Returns:
            Recommended spacing in meters (0.5λ)
        """
        wavelength = SPEED_OF_LIGHT / frequency_hz
        return wavelength * 0.5
    
    def bearing_to_compass(self, bearing_deg: float, array_orientation_deg: float = 0) -> Tuple[float, str]:
        """
        Convert relative bearing to compass bearing.
        
        Args:
            bearing_deg: Bearing relative to antenna array (0° = perpendicular to baseline)
            array_orientation_deg: Compass bearing of antenna baseline
        
        Returns:
            Tuple of (compass_bearing, cardinal_direction)
        """
        compass = (bearing_deg + array_orientation_deg) % 360
        
        # Convert to cardinal direction
        directions = [
            "North", "NNE", "NE", "ENE",
            "East", "ESE", "SE", "SSE",
            "South", "SSW", "SW", "WSW",
            "West", "WNW", "NW", "NNW"
        ]
        
        index = round(compass / 22.5) % 16
        cardinal = directions[index]
        
        return compass, cardinal
