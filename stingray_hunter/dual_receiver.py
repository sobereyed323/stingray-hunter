"""
Dual HackRF receiver coordination for direction finding.
Manages synchronized or sequential sampling from two HackRF devices.
"""

import subprocess
import numpy as np
import tempfile
import os
from typing import Tuple, Optional
from pathlib import Path


class DualReceiver:
    """Coordinate dual HackRF receivers for direction finding."""
    
    def __init__(self, hackrf_transfer_path: str = None):
        """
        Initialize dual receiver.
        
        Args:
            hackrf_transfer_path: Path to hackrf_transfer executable
        """
        if hackrf_transfer_path is None:
            # Try PothosSDR path
            pothos_path = r"C:\Program Files\PothosSDR\bin\hackrf_transfer.exe"
            self.hackrf_transfer_path = pothos_path if os.path.exists(pothos_path) else "hackrf_transfer"
        else:
            self.hackrf_transfer_path = hackrf_transfer_path
    
    def capture_dual_samples(
        self,
        frequency_hz: float,
        sample_rate_hz: int = 2000000,
        num_samples: int = 2000000,
        device1_index: int = 0,
        device2_index: int = 1
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Capture IQ samples from both HackRFs.
        
        Since we can't truly simultaneously capture, we do sequential captures
        which works well for continuous signals like cell towers.
        
        Args:
            frequency_hz: Frequency to tune to
            sample_rate_hz: Sample rate (default 2 MSPS)
            num_samples: Number of samples to capture
            device1_index: HackRF device index for receiver 1
            device2_index: HackRF device index for receiver 2
        
        Returns:
            Tuple of (iq_samples_1, iq_samples_2) as complex numpy arrays
        """
        # Capture from device 1
        samples1 = self._capture_single(
            frequency_hz,
            sample_rate_hz,
            num_samples,
            device1_index
        )
        
        # Capture from device 2
        samples2 = self._capture_single(
            frequency_hz,
            sample_rate_hz,
            num_samples,
            device2_index
        )
        
        return samples1, samples2
    
    def _capture_single(
        self,
        frequency_hz: float,
        sample_rate_hz: int,
        num_samples: int,
        device_index: int
    ) -> Optional[np.ndarray]:
        """
        Capture IQ samples from a single HackRF.
        
        Args:
            frequency_hz: Frequency to tune to
            sample_rate_hz: Sample rate
            num_samples: Number of samples
            device_index: HackRF device index
        
        Returns:
            Complex IQ samples as numpy array, or None on error
        """
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as tmp:
            tmp_path = tmp.name
        
        try:
            # Run hackrf_transfer to capture
            cmd = [
                self.hackrf_transfer_path,
                "-r", tmp_path,
                "-f", str(int(frequency_hz)),
                "-s", str(sample_rate_hz),
                "-n", str(num_samples),
                "-d", str(device_index)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"HackRF capture failed for device {device_index}: {result.stderr}")
                return None
            
            # Read IQ data from file
            iq_samples = self._read_iq_file(tmp_path)
            
            return iq_samples
            
        except subprocess.TimeoutExpired:
            print(f"Timeout capturing from device {device_index}")
            return None
        except Exception as e:
            print(f"Error capturing from device {device_index}: {e}")
            return None
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _read_iq_file(self, filepath: str) -> Optional[np.ndarray]:
        """
        Read IQ samples from HackRF binary file.
        
        HackRF outputs 8-bit IQ samples (I and Q interleaved).
        
        Args:
            filepath: Path to binary IQ file
        
        Returns:
            Complex numpy array of IQ samples
        """
        try:
            # Read raw bytes
            raw_data = np.fromfile(filepath, dtype=np.uint8)
            
            if len(raw_data) == 0:
                return None
            
            # Convert to signed (HackRF uses unsigned 8-bit, centered at 127.5)
            raw_data = raw_data.astype(np.float32) - 127.5
            
            # Separate I and Q
            i_samples = raw_data[0::2]  # Even indices
            q_samples = raw_data[1::2]  # Odd indices
            
            # Create complex samples
            iq_samples = i_samples + 1j * q_samples
            
            # Normalize
            iq_samples = iq_samples / 127.5
            
            return iq_samples
            
        except Exception as e:
            print(f"Error reading IQ file: {e}")
            return None
    
    def estimate_signal_strength(self, iq_samples: np.ndarray) -> float:
        """
        Estimate signal strength from IQ samples.
        
        Args:
            iq_samples: Complex IQ samples
        
        Returns:
            Estimated signal strength in dBm (very approximate)
        """
        if iq_samples is None or len(iq_samples) == 0:
            return -100.0
        
        # Calculate power
        power = np.mean(np.abs(iq_samples) ** 2)
        
        # Convert to dB (very rough approximation)
        # This is relative to full scale, not true dBm
        if power > 0:
            power_db = 10 * np.log10(power)
            # Rough calibration to approximate dBm
            # (Would need proper calibration for accurate readings)
            power_dbm = power_db - 30  # Rough offset
        else:
            power_dbm = -100.0
        
        return power_dbm
    
    def check_device_available(self, device_index: int) -> bool:
        """
        Check if a HackRF device is available.
        
        Args:
            device_index: Device index to check
        
        Returns:
            True if device is available
        """
        hackrf_info_path = self.hackrf_transfer_path.replace("hackrf_transfer", "hackrf_info")
        
        try:
            result = subprocess.run(
                [hackrf_info_path, "-d", str(device_index)],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.returncode == 0
        except:
            return False
