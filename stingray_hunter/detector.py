"""
Anomaly Detector for identifying rogue cell towers.
Implements multiple detection strategies for IMSI catchers/Stingrays.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Set
from enum import Enum

from .config import Config, DetectionThresholds, get_carrier_name
from .scanner import CellTower
from .tower_db import TowerDatabase, TowerRecord


class ThreatLevel(Enum):
    """Threat levels for detected anomalies."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    NEW_TOWER = "new_tower"
    SIGNAL_SPIKE = "signal_spike"
    ENCRYPTION_DISABLED = "encryption_disabled"
    DOWNGRADE_ATTACK = "downgrade_attack"
    INVALID_CARRIER = "invalid_carrier"
    IDENTITY_CHANGE = "identity_change"
    FREQUENCY_ANOMALY = "frequency_anomaly"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_type: AnomalyType
    threat_level: ThreatLevel
    tower: CellTower
    tower_record: Optional[TowerRecord]
    description: str
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"[{self.threat_level.value.upper()}] {self.anomaly_type.value}: {self.description}"


class AnomalyDetector:
    """
    Detects anomalies that indicate potential rogue cell towers.
    
    Detection methods:
    1. New Tower Detection - Unknown towers appearing
    2. Signal Spike - Abnormally strong signals
    3. Encryption Analysis - Missing or weak encryption
    4. Downgrade Detection - Forcing to older technology
    5. Carrier Validation - Invalid MCC/MNC codes
    6. Identity Changes - Tower parameters changing unexpectedly
    """
    
    def __init__(self, config: Config, database: TowerDatabase):
        self.config = config
        self.thresholds = config.thresholds
        self.db = database
        
        # Cache for quick lookups
        self._baseline_ids: Set[str] = set()
        self._refresh_baseline_cache()
        
        # Track recent towers for change detection
        self._recent_towers: dict = {}
    
    def _refresh_baseline_cache(self):
        """Refresh the baseline tower ID cache."""
        baseline = self.db.get_baseline_towers()
        self._baseline_ids = {t.unique_id for t in baseline}
    
    def analyze(self, towers: List[CellTower]) -> List[Anomaly]:
        """
        Analyze a list of detected towers for anomalies.
        Returns list of detected anomalies.
        """
        anomalies = []
        
        for tower in towers:
            # Run all detection methods
            anomalies.extend(self._check_new_tower(tower))
            anomalies.extend(self._check_signal_spike(tower))
            anomalies.extend(self._check_encryption(tower))
            anomalies.extend(self._check_carrier(tower))
            anomalies.extend(self._check_identity_change(tower))
            
            # Update recent towers cache
            self._recent_towers[tower.unique_id] = tower
        
        # Check for downgrade attacks across all towers
        anomalies.extend(self._check_downgrade(towers))
        
        # Mark suspicious towers in database
        for anomaly in anomalies:
            if anomaly.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
                self.db.mark_suspicious(
                    anomaly.tower.unique_id,
                    is_suspicious=True,
                    notes=anomaly.description
                )
        
        return anomalies
    
    def _check_new_tower(self, tower: CellTower) -> List[Anomaly]:
        """Check if this is a previously unseen tower."""
        anomalies = []
        
        if tower.unique_id not in self._baseline_ids:
            record = self.db.get_tower(tower.unique_id)
            
            if record is None:
                # Completely new tower
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.NEW_TOWER,
                    threat_level=ThreatLevel.MEDIUM,
                    tower=tower,
                    tower_record=None,
                    description=f"New tower detected: {tower.unique_id}",
                    details={
                        "frequency": tower.frequency_mhz,
                        "signal": tower.signal_strength,
                        "carrier": tower.carrier_name or "Unknown",
                    }
                ))
            elif record.times_seen < 3:
                # Rarely seen tower
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.NEW_TOWER,
                    threat_level=ThreatLevel.LOW,
                    tower=tower,
                    tower_record=record,
                    description=f"Rarely seen tower: {tower.unique_id} (seen {record.times_seen} times)",
                ))
        
        return anomalies
    
    def _check_signal_spike(self, tower: CellTower) -> List[Anomaly]:
        """Check for abnormally strong signals."""
        anomalies = []
        
        # Absolute threshold check
        if tower.signal_strength > self.thresholds.max_signal_strength:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.SIGNAL_SPIKE,
                threat_level=ThreatLevel.HIGH,
                tower=tower,
                tower_record=None,
                description=f"Abnormally strong signal: {tower.signal_strength:.1f} dBm",
                details={"signal_strength": tower.signal_strength}
            ))
        
        # Delta from baseline check
        record = self.db.get_tower(tower.unique_id)
        if record and record.is_baseline:
            delta = tower.signal_strength - record.avg_signal
            if delta > self.thresholds.signal_spike_delta:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.SIGNAL_SPIKE,
                    threat_level=ThreatLevel.MEDIUM,
                    tower=tower,
                    tower_record=record,
                    description=f"Signal spike: {delta:.1f} dB above average",
                    details={
                        "current": tower.signal_strength,
                        "average": record.avg_signal,
                        "delta": delta,
                    }
                ))
        
        return anomalies
    
    def _check_encryption(self, tower: CellTower) -> List[Anomaly]:
        """Check for missing or weak encryption."""
        anomalies = []
        
        if tower.encryption:
            # Check for no encryption
            if tower.encryption.lower() in ("none", "a5/0", "disabled"):
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.ENCRYPTION_DISABLED,
                    threat_level=ThreatLevel.CRITICAL,
                    tower=tower,
                    tower_record=self.db.get_tower(tower.unique_id),
                    description="Cell tower has encryption DISABLED!",
                    details={"encryption": tower.encryption}
                ))
            
            # Check for weak encryption (A5/1 is broken)
            elif tower.encryption.lower() == "a5/1":
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.ENCRYPTION_DISABLED,
                    threat_level=ThreatLevel.MEDIUM,
                    tower=tower,
                    tower_record=self.db.get_tower(tower.unique_id),
                    description="Cell tower using weak A5/1 encryption",
                    details={"encryption": tower.encryption}
                ))
        
        return anomalies
    
    def _check_carrier(self, tower: CellTower) -> List[Anomaly]:
        """Check for invalid carrier codes."""
        anomalies = []
        
        # Skip if we don't have MCC/MNC
        if tower.mcc == "unknown" or tower.mnc == "unknown":
            return anomalies
        
        carrier = get_carrier_name(tower.mcc, tower.mnc)
        
        if carrier is None:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.INVALID_CARRIER,
                threat_level=ThreatLevel.HIGH,
                tower=tower,
                tower_record=self.db.get_tower(tower.unique_id),
                description=f"Unknown carrier: MCC={tower.mcc}, MNC={tower.mnc}",
                details={"mcc": tower.mcc, "mnc": tower.mnc}
            ))
        
        return anomalies
    
    def _check_identity_change(self, tower: CellTower) -> List[Anomaly]:
        """Check if a known tower changed its identity parameters."""
        anomalies = []
        
        previous = self._recent_towers.get(tower.unique_id)
        if previous:
            changes = []
            
            # Check for frequency change
            if abs(previous.frequency_mhz - tower.frequency_mhz) > 0.5:
                changes.append(f"frequency: {previous.frequency_mhz} -> {tower.frequency_mhz}")
            
            # Check for technology change
            if previous.technology != tower.technology:
                changes.append(f"technology: {previous.technology} -> {tower.technology}")
            
            if changes:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.IDENTITY_CHANGE,
                    threat_level=ThreatLevel.HIGH,
                    tower=tower,
                    tower_record=self.db.get_tower(tower.unique_id),
                    description=f"Tower parameters changed: {', '.join(changes)}",
                    details={"changes": changes}
                ))
        
        return anomalies
    
    def _check_downgrade(self, towers: List[CellTower]) -> List[Anomaly]:
        """
        Check for downgrade attacks.
        If we see only 2G towers when 4G should be available, that's suspicious.
        """
        anomalies = []
        
        technologies = {t.technology for t in towers}
        
        # If only GSM (2G) present when we usually see LTE
        baseline_techs = set()
        for record in self.db.get_baseline_towers():
            baseline_techs.add(record.technology)
        
        if "LTE" in baseline_techs and "LTE" not in technologies and "GSM" in technologies:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DOWNGRADE_ATTACK,
                threat_level=ThreatLevel.HIGH,
                tower=towers[0] if towers else CellTower(
                    mcc="unknown", mnc="unknown", lac="unknown",
                    cell_id="unknown", frequency_mhz=0, signal_strength=0,
                    technology="GSM"
                ),
                tower_record=None,
                description="Possible downgrade attack: Only 2G available, LTE missing",
                details={
                    "current_tech": list(technologies),
                    "baseline_tech": list(baseline_techs),
                }
            ))
        
        return anomalies
    
    def get_threat_summary(self, anomalies: List[Anomaly]) -> dict:
        """Get summary statistics of detected anomalies."""
        summary = {
            "total": len(anomalies),
            "by_level": {level.value: 0 for level in ThreatLevel},
            "by_type": {atype.value: 0 for atype in AnomalyType},
            "critical_anomalies": [],
        }
        
        for anomaly in anomalies:
            summary["by_level"][anomaly.threat_level.value] += 1
            summary["by_type"][anomaly.anomaly_type.value] += 1
            
            if anomaly.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
                summary["critical_anomalies"].append(str(anomaly))
        
        return summary
