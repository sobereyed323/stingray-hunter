#!/usr/bin/env python3
"""Quick test to enumerate all HackRF devices"""

import subprocess
import sys

print("="*60)
print("  DUAL HACKRF DETECTION TEST")
print("="*60)

hackrf_info_path = r"C:\Program Files\PothosSDR\bin\hackrf_info.exe"

# Test indices 0 and 1 to see if both are detected
for i in range(2):
    print(f"\nTrying device index {i}...")
    try:
        result = subprocess.run(
            [hackrf_info_path, "-d", str(i)],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if result.returncode == 0:
            # Parse serial number
            for line in result.stdout.split('\n'):
                if 'Serial number:' in line:
                    serial = line.split(':')[1].strip()
                    print(f"  ✓ FOUND: Serial {serial}")
                elif 'Firmware Version:' in line:
                    firmware = line.split(':')[1].strip()
                    print(f"    Firmware: {firmware}")
        else:
            print(f"  ✗ No device at index {i}")
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout at index {i}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "="*60)
print("SUMMARY:")

# Run without device flag to see what's found
result = subprocess.run([hackrf_info_path], capture_output=True, text=True, timeout=3)
device_count = result.stdout.count("Serial number:")
print(f"Total HackRF devices detected: {device_count}")
print("="*60)
