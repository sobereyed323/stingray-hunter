# 🛰️ Stingray Hunter

**Rogue Cell Tower Detection Toolkit** - A dual-HackRF system for detecting IMSI catchers and Stingrays.

## ⚠️ Legal Notice

This toolkit is for **security research and personal protection only**. Transmitting on cellular frequencies is illegal without a license. This system operates in **receive-only mode**.

## 🔧 Requirements

### Hardware
- 1-2x HackRF One devices
- USB-C to USB-A adapters (data-capable)
- Recommended: Powered USB hub

### Software
- Python 3.8+
- HackRF tools (`hackrf_info`, `hackrf_sweep`)
- Optional: `kalibrate-hackrf` for GSM detection

## 📦 Installation

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Verify HackRF is detected
hackrf_info
```

## 🚀 Usage

```powershell
# Check device status
python cli.py status

# Run a single scan
python cli.py scan

# Run continuous scanning
python cli.py scan --continuous

# Mark current towers as baseline (known good)
python cli.py baseline

# View detection report
python cli.py report
```

## 🎯 Detection Methods

| Method | Description |
|--------|-------------|
| **New Tower** | Unknown Cell ID appearing |
| **Signal Spike** | Abnormally strong signal |
| **Encryption Disabled** | No A5/1 encryption |
| **Downgrade Attack** | 2G-only when 4G available |
| **Invalid Carrier** | Wrong MCC/MNC codes |

## 📁 Project Structure

```
stingray_hunter/
├── config.py          # Configuration & frequency bands
├── device_manager.py  # Multi-HackRF handling
├── scanner.py         # Cell tower scanning
├── tower_db.py        # SQLite tower database
├── detector.py        # Anomaly detection
└── alerts.py          # Alert system
```

## 🔬 Workflow

1. **Baseline**: When in a safe location, run `baseline` to mark known towers
2. **Scan**: Run continuous scans while moving through an area
3. **Investigate**: Review alerts and suspicious towers in reports

---

Made for security research. Use responsibly. 🛡️
