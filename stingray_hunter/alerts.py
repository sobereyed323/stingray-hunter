"""
Alert System for notifying about detected anomalies.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from .detector import Anomaly, ThreatLevel


class ConsoleAlertHandler:
    """Outputs alerts to console with colors."""
    
    COLORS = {
        ThreatLevel.INFO: "\033[36m",
        ThreatLevel.LOW: "\033[32m",
        ThreatLevel.MEDIUM: "\033[33m",
        ThreatLevel.HIGH: "\033[91m",
        ThreatLevel.CRITICAL: "\033[95m",
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def send(self, anomaly: Anomaly) -> bool:
        color = self.COLORS.get(anomaly.threat_level, "")
        print(f"\n{self.BOLD}{'='*60}{self.RESET}")
        print(f"{color}{self.BOLD}⚠️  ALERT: {anomaly.threat_level.value.upper()}{self.RESET}")
        print(f"{self.BOLD}Type:{self.RESET} {anomaly.anomaly_type.value}")
        print(f"{self.BOLD}Tower:{self.RESET} {anomaly.tower.unique_id}")
        print(f"{self.BOLD}Description:{self.RESET} {anomaly.description}")
        if anomaly.details:
            for key, value in anomaly.details.items():
                print(f"  • {key}: {value}")
        return True


class SoundAlertHandler:
    """Plays sound alerts for high-priority anomalies."""
    
    def send(self, anomaly: Anomaly) -> bool:
        if anomaly.threat_level not in (ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL):
            return False
        try:
            import winsound
            if anomaly.threat_level == ThreatLevel.CRITICAL:
                for _ in range(3):
                    winsound.Beep(1000, 200)
            elif anomaly.threat_level == ThreatLevel.HIGH:
                winsound.Beep(800, 300)
            else:
                winsound.Beep(600, 200)
            return True
        except:
            print('\a')
            return True


class FileAlertHandler:
    """Logs alerts to JSON file."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def send(self, anomaly: Anomaly) -> bool:
        log_file = self.log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        alerts = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                alerts = json.load(f)
        
        alerts.append({
            "timestamp": anomaly.timestamp.isoformat(),
            "threat_level": anomaly.threat_level.value,
            "anomaly_type": anomaly.anomaly_type.value,
            "tower_id": anomaly.tower.unique_id,
            "description": anomaly.description,
        })
        
        with open(log_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        return True


class AlertSystem:
    """Manages alert handlers."""
    
    def __init__(self, console: bool = True, sound: bool = True, log_dir: Optional[Path] = None):
        self.handlers = []
        if console:
            self.handlers.append(ConsoleAlertHandler())
        if sound:
            self.handlers.append(SoundAlertHandler())
        if log_dir:
            self.handlers.append(FileAlertHandler(log_dir))
    
    def alert(self, anomaly: Anomaly) -> None:
        for handler in self.handlers:
            handler.send(anomaly)
    
    def alert_all(self, anomalies: List[Anomaly]) -> int:
        for anomaly in anomalies:
            self.alert(anomaly)
        return len(anomalies)
