"""
Device Manager for multiple HackRF devices.
Handles enumeration, configuration, and role assignment.
"""

import subprocess
import re
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class DeviceRole(Enum):
    """Roles a HackRF can take."""
    GSM_SCANNER = "gsm_scanner"
    LTE_SCANNER = "lte_scanner"
    MONITOR = "monitor"
    IDLE = "idle"


@dataclass
class HackRFDevice:
    """Represents a connected HackRF device."""
    index: int
    serial: str
    board_id: str
    firmware_version: str
    part_id: str
    role: DeviceRole = DeviceRole.IDLE
    is_portapack: bool = False
    
    def __str__(self):
        pp = " [PortaPack]" if self.is_portapack else ""
        return f"HackRF #{self.index}: {self.serial}{pp} ({self.role.value})"


class DeviceManager:
    """Manages multiple HackRF devices."""
    
    def __init__(self):
        self.devices: Dict[int, HackRFDevice] = {}
        # Try PothosSDR path on Windows, fallback to PATH
        import os
        pothos_path = r"C:\Program Files\PothosSDR\bin\hackrf_info.exe"
        self._hackrf_path = pothos_path if os.path.exists(pothos_path) else "hackrf_info"
    
    def enumerate_devices(self) -> List[HackRFDevice]:
        """
        Enumerate all connected HackRF devices.
        Returns a list of unique devices found.
        """
        self.devices.clear()
        seen_serials = set()
        consecutive_failures = 0
        max_consecutive_failures = 3  # Stop after 3 consecutive failures
        
        # Try up to 10 device indices
        for device_index in range(10):
            device = self._probe_device(device_index)
            
            if device:
                # Only add if we haven't seen this serial before
                if device.serial not in seen_serials:
                    self.devices[device_index] = device
                    seen_serials.add(device.serial)
                    print(f"Found unique device at index {device_index}: {device.serial}")
                    consecutive_failures = 0  # Reset failure counter
                else:
                    print(f"Skipping duplicate device at index {device_index}: {device.serial}")
            else:
                consecutive_failures += 1
                # Only stop if we have multiple consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    break
        
        return list(self.devices.values())
    
    def _probe_device(self, index: int) -> Optional[HackRFDevice]:
        """Probe a specific device index."""
        try:
            result = subprocess.run(
                [self._hackrf_path, "-d", str(index)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            output = result.stdout
            
            # Parse hackrf_info output
            serial = self._extract_field(output, r"Serial number:\s*(\S+)")
            board_id = self._extract_field(output, r"Board ID Number:\s*(\d+)")
            firmware = self._extract_field(output, r"Firmware Version:\s*(.+)")
            part_id = self._extract_field(output, r"Part ID Number:\s*(\S+)")
            
            if not serial:
                return None
            
            # Detect PortaPack (usually shows in firmware or additional fields)
            is_portapack = "portapack" in output.lower() or "mayhem" in output.lower()
            
            return HackRFDevice(
                index=index,
                serial=serial,
                board_id=board_id or "unknown",
                firmware_version=firmware or "unknown",
                part_id=part_id or "unknown",
                is_portapack=is_portapack
            )
            
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            raise RuntimeError(
                "hackrf_info not found. Please install HackRF tools.\n"
                "Windows: Download from https://github.com/greatscottgadgets/hackrf/releases"
            )
    
    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        """Extract a field from hackrf_info output using regex."""
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    def assign_roles(self, auto: bool = True) -> None:
        """
        Assign roles to devices.
        If auto=True, automatically assigns based on PortaPack presence.
        """
        if not self.devices:
            raise RuntimeError("No devices found. Call enumerate_devices() first.")
        
        if auto:
            # PortaPack device gets first role, bare HackRF gets second
            for device in self.devices.values():
                if device.is_portapack:
                    device.role = DeviceRole.GSM_SCANNER
                else:
                    device.role = DeviceRole.LTE_SCANNER
            
            # If only one device or no PortaPack, assign GSM scanner first
            if len(self.devices) == 1:
                list(self.devices.values())[0].role = DeviceRole.GSM_SCANNER
            elif not any(d.is_portapack for d in self.devices.values()):
                devices_list = list(self.devices.values())
                devices_list[0].role = DeviceRole.GSM_SCANNER
                if len(devices_list) > 1:
                    devices_list[1].role = DeviceRole.LTE_SCANNER
    
    def get_device_by_role(self, role: DeviceRole) -> Optional[HackRFDevice]:
        """Get device assigned to a specific role."""
        for device in self.devices.values():
            if device.role == role:
                return device
        return None
    
    def get_device_by_index(self, index: int) -> Optional[HackRFDevice]:
        """Get device by its index."""
        return self.devices.get(index)
    
    def status(self) -> str:
        """Get human-readable status of all devices."""
        if not self.devices:
            return "No HackRF devices detected."
        
        lines = ["=== HackRF Devices ==="]
        for device in self.devices.values():
            lines.append(str(device))
            lines.append(f"    Firmware: {device.firmware_version}")
            lines.append(f"    Serial: {device.serial}")
        return "\n".join(lines)


# Convenience function for quick device check
def check_hackrf_available() -> bool:
    """Quick check if any HackRF is connected."""
    import os
    pothos_path = r"C:\Program Files\PothosSDR\bin\hackrf_info.exe"
    hackrf_cmd = pothos_path if os.path.exists(pothos_path) else "hackrf_info"
    try:
        result = subprocess.run(
            [hackrf_cmd],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
