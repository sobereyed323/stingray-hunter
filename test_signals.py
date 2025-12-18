#!/usr/bin/env python3
"""Quick test to see what signals we're receiving"""

import subprocess
import re

print("Testing LTE signal reception on key frequencies...")
print("="*60)

frequencies = [
    (869, "GSM 850 / LTE Band 5"),
    (890, "GSM 850 uplink"),
    (1930, "LTE Band 2 / PCS"),
    (1950, "LTE Band 2 center"),
    (1970, "LTE Band 2"),
]

for freq_mhz, name in frequencies:
    cmd = [
        r"C:\Program Files\PothosSDR\bin\hackrf_transfer.exe",
        "-r", "temp.bin",
        "-f", str(int(freq_mhz * 1_000_000)),
        "-s", "2000000",
        "-n", "200000",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    
    if result.returncode == 0:
        match = re.search(r'amplitude\s+([-\d.]+)\s+dBfs', result.stdout)
        if match:
            signal = match.group(1)
            print(f"{freq_mhz:4.0f} MHz - {name:30s} : {signal:>6s} dBfs")
        else:
            print(f"{freq_mhz:4.0f} MHz - {name:30s} : No signal")
    else:
        print(f"{freq_mhz:4.0f} MHz - {name:30s} : ERROR")

print("="*60)
print("\nSignals above -20 dBfs indicate strong cell towers!")
