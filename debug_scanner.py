#!/usr/bin/env python3
"""Debug script to see exactly what the scanner is receiving"""

import sys
sys.path.insert(0, '.')

from stingray_hunter.config import Config
from stingray_hunter.device_manager import DeviceManager
from stingray_hunter.scanner import Scanner

print("="*60)
print("  STINGRAY HUNTER - DEBUG MODE")
print("="*60)

# Initialize
config = Config.default()
dm = DeviceManager()
devices = dm.enumerate_devices()

if not devices:
    print("❌ No HackRF detected!")
    exit(1)

print(f"✓ HackRF detected: {devices[0].serial}")
print()

scanner = Scanner(config, devices[0])

# Test a single band
print("Testing GSM 850 band (869-894 MHz)...")
print("-"*60)

samples = scanner.sweep_spectrum(869, 894, 1000000)

print(f"Received {len(samples)} spectrum samples")
print()

if samples:
    print("Sample signals:")
    for i, sample in enumerate(samples[:10]):  # Show first 10
        print(f"  {sample.frequency_mhz:7.1f} MHz: {sample.power_db:6.1f} dB")
    
    print()
    print("Signal statistics:")
    powers = [s.power_db for s in samples]
    print(f"  Min signal:    {min(powers):6.1f} dB")
    print(f"  Max signal:    {max(powers):6.1f} dB")
    print(f"  Median signal: {sorted(powers)[len(powers)//2]:6.1f} dB")
    
    # Check detection threshold
    noise_floor = sorted(powers)[len(powers) // 2]
    threshold = noise_floor + 10  # Current threshold
    
    print()
    print("Detection parameters:")
    print(f"  Noise floor:  {noise_floor:6.1f} dB")
    print(f"  Threshold:    {threshold:6.1f} dB (noise + 10 dB)")
    
    above_threshold = [s for s in samples if s.power_db > threshold]
    print(f"  Signals above threshold: {len(above_threshold)}")
    
    if above_threshold:
        print()
        print("Signals that should be detected:")
        for sample in above_threshold[:5]:
            print(f"  {sample.frequency_mhz:7.1f} MHz: {sample.power_db:6.1f} dB")
    
    # Now run detection
    print()
    print("-"*60)
    print("Running tower detection algorithm...")
    towers = scanner._detect_towers_from_sweep("GSM_850", 869, 894)
    
    print(f"Detected {len(towers)} towers")
    if towers:
        for tower in towers:
            print(f"  Tower: {tower.frequency_mhz:.1f} MHz, {tower.signal_strength:.1f} dB")
    else:
        print("  ❌ No towers detected!")
        print()
        print("Possible issues:")
        print("  - Not enough consecutive samples above threshold")
        print("  - Peak grouping algorithm not working")
        print("  - Detection threshold too high")
else:
    print("❌ No samples received! Check HackRF connection.")

print("="*60)
