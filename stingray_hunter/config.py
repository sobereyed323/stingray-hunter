"""
Configuration management for Stingray Hunter.
Defines frequency bands, detection thresholds, and device settings.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class FrequencyBand:
    """Represents a cellular frequency band."""
    name: str
    start_mhz: float
    end_mhz: float
    technology: str  # GSM, LTE, 5G


# US Cellular Frequency Bands
FREQUENCY_BANDS = {
    # GSM Bands
    "GSM_850": FrequencyBand("GSM 850", 824.0, 894.0, "GSM"),
    "GSM_1900": FrequencyBand("GSM 1900 (PCS)", 1850.0, 1990.0, "GSM"),
    
    # LTE Bands (Common US)
    "LTE_B2": FrequencyBand("LTE Band 2 (PCS)", 1850.0, 1990.0, "LTE"),
    "LTE_B4": FrequencyBand("LTE Band 4 (AWS)", 1710.0, 2155.0, "LTE"),
    "LTE_B5": FrequencyBand("LTE Band 5 (850)", 824.0, 894.0, "LTE"),
    "LTE_B12": FrequencyBand("LTE Band 12 (700)", 699.0, 746.0, "LTE"),
    "LTE_B13": FrequencyBand("LTE Band 13 (700)", 746.0, 787.0, "LTE"),
    "LTE_B66": FrequencyBand("LTE Band 66 (AWS-3)", 1710.0, 2200.0, "LTE"),
    "LTE_B71": FrequencyBand("LTE Band 71 (600)", 617.0, 698.0, "LTE"),
}

# Major US Carrier MCC/MNC codes
US_CARRIERS = {
    ("310", "410"): "AT&T",
    ("310", "260"): "T-Mobile",
    ("311", "480"): "Verizon",
    ("310", "120"): "Sprint",
    ("312", "530"): "US Cellular",
}


@dataclass
class DetectionThresholds:
    """Thresholds for anomaly detection."""
    # Signal strength (dBm) - above this is suspiciously strong
    max_signal_strength: float = -30.0
    
    # Minimum time (seconds) a tower should be seen before considered "known"
    min_known_time: int = 3600
    
    # How much stronger (dB) than normal is suspicious
    signal_spike_delta: float = 20.0
    
    # Alert if tower disappears and reappears with different params
    identity_change_window: int = 300


@dataclass
class DeviceConfig:
    """Configuration for a HackRF device."""
    serial: Optional[str] = None
    role: str = "scanner"  # scanner, monitor
    frequency_bands: List[str] = field(default_factory=lambda: ["GSM_850", "GSM_1900"])
    sample_rate: int = 2_000_000
    lna_gain: int = 32
    vga_gain: int = 20


@dataclass
class Config:
    """Main configuration for Stingray Hunter."""
    # Project paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    scan_log_dir: Path = field(default_factory=lambda: Path("data/scans"))
    database_path: Path = field(default_factory=lambda: Path("data/towers.db"))
    
    # Detection settings
    thresholds: DetectionThresholds = field(default_factory=DetectionThresholds)
    
    # Device configurations
    devices: List[DeviceConfig] = field(default_factory=list)
    
    # Scanning settings
    scan_interval: float = 1.0  # seconds between sweeps
    continuous_scan: bool = True
    
    # Alerting
    alert_sound: bool = True
    alert_log: bool = True
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scan_log_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, path: Path):
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path) -> 'Config':
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct nested dataclasses
        data['data_dir'] = Path(data['data_dir'])
        data['scan_log_dir'] = Path(data['scan_log_dir'])
        data['database_path'] = Path(data['database_path'])
        data['thresholds'] = DetectionThresholds(**data['thresholds'])
        data['devices'] = [DeviceConfig(**d) for d in data['devices']]
        
        return cls(**data)
    
    @classmethod
    def default(cls) -> 'Config':
        """Create default configuration with two HackRF devices."""
        return cls(
            devices=[
                DeviceConfig(role="gsm_scanner", frequency_bands=["GSM_850", "GSM_1900"]),
                DeviceConfig(role="lte_scanner", frequency_bands=["LTE_B2", "LTE_B4", "LTE_B12"]),
            ]
        )


def get_carrier_name(mcc: str, mnc: str) -> Optional[str]:
    """Look up carrier name from MCC/MNC codes."""
    return US_CARRIERS.get((mcc, mnc))


def get_frequency_band(freq_mhz: float) -> Optional[FrequencyBand]:
    """Find which frequency band contains the given frequency."""
    for band in FREQUENCY_BANDS.values():
        if band.start_mhz <= freq_mhz <= band.end_mhz:
            return band
    return None
