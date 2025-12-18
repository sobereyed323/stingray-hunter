"""
Tower Database for tracking and baselining cell towers.
Uses SQLite for persistent storage.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .scanner import CellTower


@dataclass
class TowerRecord:
    """Extended tower record with history."""
    unique_id: str
    mcc: str
    mnc: str
    lac: str
    cell_id: str
    frequency_mhz: float
    technology: str
    carrier_name: Optional[str]
    
    # Stats
    first_seen: datetime
    last_seen: datetime
    times_seen: int
    avg_signal: float
    min_signal: float
    max_signal: float
    
    # Baseline status
    is_baseline: bool = False
    is_suspicious: bool = False
    notes: str = ""


class TowerDatabase:
    """SQLite database for cell tower tracking."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS towers (
                    unique_id TEXT PRIMARY KEY,
                    mcc TEXT,
                    mnc TEXT,
                    lac TEXT,
                    cell_id TEXT,
                    frequency_mhz REAL,
                    technology TEXT,
                    carrier_name TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    times_seen INTEGER DEFAULT 1,
                    avg_signal REAL,
                    min_signal REAL,
                    max_signal REAL,
                    is_baseline INTEGER DEFAULT 0,
                    is_suspicious INTEGER DEFAULT 0,
                    notes TEXT DEFAULT ''
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sightings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tower_id TEXT,
                    timestamp TEXT,
                    signal_strength REAL,
                    arfcn INTEGER,
                    encryption TEXT,
                    FOREIGN KEY (tower_id) REFERENCES towers(unique_id)
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sightings_tower 
                ON sightings(tower_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sightings_time 
                ON sightings(timestamp)
            ''')
            
            # Location measurements for triangulation
            conn.execute('''
                CREATE TABLE IF NOT EXISTS location_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tower_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    signal_strength REAL,
                    timestamp TEXT,
                    scan_id TEXT,
                    FOREIGN KEY (tower_id) REFERENCES towers(unique_id)
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_location_tower 
                ON location_measurements(tower_id)
            ''')
            
            conn.commit()
    
    def record_tower(self, tower: CellTower) -> TowerRecord:
        """
        Record a tower sighting.
        Updates existing record or creates new one.
        Returns the tower record.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Check if tower exists
            existing = conn.execute(
                'SELECT * FROM towers WHERE unique_id = ?',
                (tower.unique_id,)
            ).fetchone()
            
            now = datetime.now().isoformat()
            
            if existing:
                # Update existing tower
                new_times = existing['times_seen'] + 1
                
                # Rolling average for signal strength
                new_avg = (
                    (existing['avg_signal'] * existing['times_seen'] + tower.signal_strength) 
                    / new_times
                )
                new_min = min(existing['min_signal'], tower.signal_strength)
                new_max = max(existing['max_signal'], tower.signal_strength)
                
                conn.execute('''
                    UPDATE towers SET
                        last_seen = ?,
                        times_seen = ?,
                        avg_signal = ?,
                        min_signal = ?,
                        max_signal = ?
                    WHERE unique_id = ?
                ''', (now, new_times, new_avg, new_min, new_max, tower.unique_id))
                
            else:
                # Insert new tower
                conn.execute('''
                    INSERT INTO towers (
                        unique_id, mcc, mnc, lac, cell_id, frequency_mhz,
                        technology, carrier_name, first_seen, last_seen,
                        times_seen, avg_signal, min_signal, max_signal
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                ''', (
                    tower.unique_id, tower.mcc, tower.mnc, tower.lac,
                    tower.cell_id, tower.frequency_mhz, tower.technology,
                    tower.carrier_name, now, now, tower.signal_strength,
                    tower.signal_strength, tower.signal_strength
                ))
            
            # Record the sighting
            conn.execute('''
                INSERT INTO sightings (tower_id, timestamp, signal_strength, arfcn, encryption)
                VALUES (?, ?, ?, ?, ?)
            ''', (tower.unique_id, now, tower.signal_strength, tower.arfcn, tower.encryption))
            
            conn.commit()
            
            return self.get_tower(tower.unique_id)
    
    def get_tower(self, unique_id: str) -> Optional[TowerRecord]:
        """Get a tower record by unique ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            row = conn.execute(
                'SELECT * FROM towers WHERE unique_id = ?',
                (unique_id,)
            ).fetchone()
            
            if row:
                return self._row_to_record(row)
            return None
    
    def _row_to_record(self, row: sqlite3.Row) -> TowerRecord:
        """Convert database row to TowerRecord."""
        return TowerRecord(
            unique_id=row['unique_id'],
            mcc=row['mcc'],
            mnc=row['mnc'],
            lac=row['lac'],
            cell_id=row['cell_id'],
            frequency_mhz=row['frequency_mhz'],
            technology=row['technology'],
            carrier_name=row['carrier_name'],
            first_seen=datetime.fromisoformat(row['first_seen']),
            last_seen=datetime.fromisoformat(row['last_seen']),
            times_seen=row['times_seen'],
            avg_signal=row['avg_signal'],
            min_signal=row['min_signal'],
            max_signal=row['max_signal'],
            is_baseline=bool(row['is_baseline']),
            is_suspicious=bool(row['is_suspicious']),
            notes=row['notes'] or "",
        )
    
    def get_all_towers(self) -> List[TowerRecord]:
        """Get all recorded towers."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute('SELECT * FROM towers ORDER BY last_seen DESC').fetchall()
            return [self._row_to_record(row) for row in rows]
    
    def get_baseline_towers(self) -> List[TowerRecord]:
        """Get all towers marked as baseline (known good)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute(
                'SELECT * FROM towers WHERE is_baseline = 1'
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def get_suspicious_towers(self) -> List[TowerRecord]:
        """Get all towers marked as suspicious."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute(
                'SELECT * FROM towers WHERE is_suspicious = 1 ORDER BY last_seen DESC'
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def get_new_towers(self, since: timedelta = timedelta(hours=24)) -> List[TowerRecord]:
        """Get towers first seen within the specified time period."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            threshold = (datetime.now() - since).isoformat()
            
            rows = conn.execute(
                'SELECT * FROM towers WHERE first_seen > ? AND is_baseline = 0 ORDER BY first_seen DESC',
                (threshold,)
            ).fetchall()
            
            return [self._row_to_record(row) for row in rows]
    
    def mark_baseline(self, unique_id: str, is_baseline: bool = True) -> None:
        """Mark a tower as baseline (known good)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE towers SET is_baseline = ? WHERE unique_id = ?',
                (int(is_baseline), unique_id)
            )
            conn.commit()
    
    def mark_suspicious(self, unique_id: str, is_suspicious: bool = True, notes: str = "") -> None:
        """Mark a tower as suspicious."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE towers SET is_suspicious = ?, notes = ? WHERE unique_id = ?',
                (int(is_suspicious), notes, unique_id)
            )
            conn.commit()
    
    def baseline_all_current(self) -> int:
        """Mark all currently known towers as baseline. Returns count."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('UPDATE towers SET is_baseline = 1')
            conn.commit()
            return cursor.rowcount
    
    def get_tower_history(
        self, 
        unique_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get signal history for a tower."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute('''
                SELECT * FROM sightings 
                WHERE tower_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (unique_id, limit)).fetchall()
            
            return [dict(row) for row in rows]
    
    def stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute('SELECT COUNT(*) FROM towers').fetchone()[0]
            baseline = conn.execute(
                'SELECT COUNT(*) FROM towers WHERE is_baseline = 1'
            ).fetchone()[0]
            suspicious = conn.execute(
                'SELECT COUNT(*) FROM towers WHERE is_suspicious = 1'
            ).fetchone()[0]
            sightings = conn.execute('SELECT COUNT(*) FROM sightings').fetchone()[0]
            
            return {
                "total_towers": total,
                "baseline_towers": baseline,
                "suspicious_towers": suspicious,
                "total_sightings": sightings,
            }
    
    def record_location_measurement(
        self, 
        tower_id: str, 
        latitude: float, 
        longitude: float, 
        signal_strength: float,
        scan_id: str = None
    ) -> None:
        """Record a signal strength measurement at a specific GPS location."""
        with sqlite3.connect(self.db_path) as conn:
            timestamp = datetime.now().isoformat()
            if not scan_id:
                scan_id = timestamp
            
            conn.execute('''
                INSERT INTO location_measurements 
                (tower_id, latitude, longitude, signal_strength, timestamp, scan_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tower_id, latitude, longitude, signal_strength, timestamp, scan_id))
            conn.commit()
    
    def get_location_measurements(self, tower_id: str) -> List[Dict[str, Any]]:
        """Get all location measurements for a tower."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute('''
                SELECT * FROM location_measurements 
                WHERE tower_id = ? 
                ORDER BY timestamp DESC
            ''', (tower_id,)).fetchall()
            
            return [dict(row) for row in rows]
