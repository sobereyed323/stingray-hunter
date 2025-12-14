"""
Cell Tower Scanner using HackRF.
Wraps hackrf_sweep and kalibrate-hackrf for tower detection.
"""

import subprocess
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Generator, Dict, Any
from pathlib import Path

from .config import Config, FREQUENCY_BANDS, get_frequency_band, get_carrier_name
from .device_manager import HackRFDevice


@dataclass
class CellTower:
    """Represents a detected cell tower."""
    # Identity
    mcc: str  # Mobile Country Code
    mnc: str  # Mobile Network Code
    lac: str  # Location Area Code
    cell_id: str  # Cell ID
    
    # Signal info
    frequency_mhz: float
    signal_strength: float  # dBm
    
    # Metadata
    technology: str  # GSM, LTE, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Optional extended info
    arfcn: Optional[int] = None  # Absolute Radio Frequency Channel Number
    encryption: Optional[str] = None  # A5/1, A5/3, etc.
    carrier_name: Optional[str] = None
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for this tower."""
        return f"{self.mcc}-{self.mnc}-{self.lac}-{self.cell_id}"
    
    def __post_init__(self):
        """Auto-fill carrier name if not provided."""
        if not self.carrier_name:
            self.carrier_name = get_carrier_name(self.mcc, self.mnc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mcc": self.mcc,
            "mnc": self.mnc,
            "lac": self.lac,
            "cell_id": self.cell_id,
            "frequency_mhz": self.frequency_mhz,
            "signal_strength": self.signal_strength,
            "technology": self.technology,
            "timestamp": self.timestamp.isoformat(),
            "arfcn": self.arfcn,
            "encryption": self.encryption,
            "carrier_name": self.carrier_name,
            "unique_id": self.unique_id,
        }


@dataclass
class SpectrumSample:
    """A single spectrum measurement."""
    frequency_mhz: float
    power_db: float
    timestamp: datetime = field(default_factory=datetime.now)


class Scanner:
    """
    Cell tower scanner using HackRF.
    Uses hackrf_sweep for spectrum analysis and kalibrate for GSM detection.
    """
    
    def __init__(self, config: Config, device: Optional[HackRFDevice] = None):
        self.config = config
        self.device = device
        self.device_index = device.index if device else 0
        
        # Tool paths (assume in PATH)
        self.hackrf_sweep_path = "hackrf_sweep"
        self.kalibrate_path = "kal"  # kalibrate-hackrf binary
        
        # Scan state
        self.is_scanning = False
        self.last_scan: List[CellTower] = []
    
    def sweep_spectrum(
        self, 
        start_mhz: float, 
        end_mhz: float,
        bin_width_hz: int = 100000
    ) -> List[SpectrumSample]:
        """
        Perform a spectrum sweep in the given range.
        Returns list of power measurements.
        """
        samples = []
        
        try:
            cmd = [
                self.hackrf_sweep_path,
                "-d", str(self.device_index),
                "-f", f"{int(start_mhz)}:{int(end_mhz)}",
                "-w", str(bin_width_hz),
                "-1",  # One sweep only
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                samples = self._parse_sweep_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            raise RuntimeError("hackrf_sweep not found. Install HackRF tools.")
        
        return samples
    
    def _parse_sweep_output(self, output: str) -> List[SpectrumSample]:
        """Parse hackrf_sweep CSV output."""
        samples = []
        now = datetime.now()
        
        for line in output.strip().split('\n'):
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) >= 6:
                try:
                    # hackrf_sweep format: date, time, hz_low, hz_high, hz_bin_width, num_samples, [dB values...]
                    hz_low = float(parts[2])
                    hz_bin_width = float(parts[4])
                    
                    # Parse power values
                    for i, db_val in enumerate(parts[6:]):
                        freq_hz = hz_low + (i * hz_bin_width)
                        freq_mhz = freq_hz / 1_000_000
                        power_db = float(db_val)
                        
                        samples.append(SpectrumSample(
                            frequency_mhz=freq_mhz,
                            power_db=power_db,
                            timestamp=now
                        ))
                except (ValueError, IndexError):
                    continue
        
        return samples
    
    def scan_gsm_band(self, band_name: str = "GSM_850") -> List[CellTower]:
        """
        Scan a GSM band for cell towers using kalibrate.
        Returns list of detected towers.
        """
        band = FREQUENCY_BANDS.get(band_name)
        if not band:
            raise ValueError(f"Unknown band: {band_name}")
        
        towers = []
        
        # Map our band names to kalibrate band names
        kal_band_map = {
            "GSM_850": "GSM850",
            "GSM_1900": "PCS",
        }
        
        kal_band = kal_band_map.get(band_name)
        if not kal_band:
            return towers  # Band not supported by kalibrate
        
        try:
            cmd = [
                self.kalibrate_path,
                "-s", kal_band,
                "-d", str(self.device_index),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                towers = self._parse_kalibrate_output(result.stdout, band)
        
        except subprocess.TimeoutExpired:
            pass
        except FileNotFoundError:
            # Kalibrate not installed - fall back to spectrum sweep
            pass
        
        return towers
    
    def _parse_kalibrate_output(self, output: str, band) -> List[CellTower]:
        """Parse kalibrate scan output."""
        towers = []
        
        # Kalibrate output format:
        # chan: 128 (869.2MHz +   34Hz) power: 1234567.89
        pattern = r'chan:\s*(\d+)\s*\((\d+\.?\d*)MHz.*\)\s*power:\s*([\d.]+)'
        
        for match in re.finditer(pattern, output):
            arfcn = int(match.group(1))
            freq_mhz = float(match.group(2))
            power = float(match.group(3))
            
            # Convert power to approximate dBm (rough estimate)
            # Note: This is a rough conversion, actual calibration needed
            signal_db = -100 + (power / 1000000) * 40  # Very rough
            
            tower = CellTower(
                mcc="unknown",
                mnc="unknown",
                lac="unknown",
                cell_id=f"ARFCN-{arfcn}",
                frequency_mhz=freq_mhz,
                signal_strength=signal_db,
                technology=band.technology,
                arfcn=arfcn,
            )
            towers.append(tower)
        
        return towers
    
    def scan_all_bands(self) -> List[CellTower]:
        """Scan all configured frequency bands."""
        all_towers = []
        
        for band_name in ["GSM_850", "GSM_1900"]:
            if band_name in FREQUENCY_BANDS:
                towers = self.scan_gsm_band(band_name)
                all_towers.extend(towers)
        
        self.last_scan = all_towers
        return all_towers
    
    def continuous_scan(self) -> Generator[List[CellTower], None, None]:
        """
        Generator for continuous scanning.
        Yields tower lists on each scan cycle.
        """
        import time
        
        self.is_scanning = True
        
        try:
            while self.is_scanning:
                towers = self.scan_all_bands()
                yield towers
                time.sleep(self.config.scan_interval)
        finally:
            self.is_scanning = False
    
    def stop(self):
        """Stop continuous scanning."""
        self.is_scanning = False
    
    def save_scan(self, towers: List[CellTower], path: Path) -> None:
        """Save scan results to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "device_index": self.device_index,
            "towers": [t.to_dict() for t in towers]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
