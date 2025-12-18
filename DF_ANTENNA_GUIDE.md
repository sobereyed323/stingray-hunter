# 🧭 Direction Finding Antenna Setup Guide

## What You Need

✅ **Two HackRF One devices** - You have these!  
✅ **Two identical antennas** - Same model, same length  
✅ **Mounting board** - To keep spacing constant (wood, plastic, or metal)  
✅ **Antenna cables** - If needed to reach both HackRFs  
✅ **Compass app** - On your phone for navigation

---

## Antenna Spacing

The spacing between your antennas determines frequency range and accuracy.

### Recommended Spacing by Band:

| Frequency Band | Wavelength | Recommended Spacing |
|---------------|------------|---------------------|
| GSM 850 MHz | 35 cm | **18 cm** (0.5λ) |
| LTE 1900 MHz | 16 cm | **8 cm** (0.5λ) |
| 5G 2500 MHz | 12 cm | **6 cm** (0.5λ) |

**Rule of thumb:** Use spacing = 0.5λ (half wavelength) for best accuracy

### Calculate for Any Frequency:
```
Spacing (meters) = (Speed of Light) / (Frequency * 2)
Spacing (meters) = 300,000,000 / (Frequency in Hz * 2)

Example for 869 MHz:
= 300,000,000 / (869,000,000 * 2)
= 0.17 meters = 17 cm
```

---

## Physical Setup

### Option A: Simple Board Mount (Easiest)

```
┌──────────────────────────────┐
│                              │ ← Wood/plastic board
│    ●         ●                │
│   Ant1     Ant2               │
│    ↓         ↓                │
│   [H1]     [H2]               │ ← HackRFs attached or cables
│                              │
└──────────────────────────────┘
```

**Steps:**
1. Get a board ~30cm x 20cm
2. Mount antennas 18cm apart (for GSM 850)
3. Keep antennas parallel and vertical
4. Attach HackRFs below or use extension cables

### Option B: Portable Frame

```
      Ant1 (●)    Ant2 (●)
        |            |
        |            |
      ┌─┴────────────┴─┐
      │  PVC/wood bar   │  ← 18cm spacing marked
      └────────┬────────┘
               │
          Handle/grip
```

**Advantages:**
- Easy to rotate for direction finding
- Portable
- Can mark different spacings for different frequencies

---

## Antenna Selection

### Best Options:

**1. Telescopic Whip Antennas** (Easiest)
- Extend to quarter-wave length
- GSM 850: ~9 cm
- LTE 1900: ~4 cm
- Inexpensive and compact

**2. Omnidirectional Antennas**
- Fixed length
- Buy TWO identical units
- Good for consistent results

**3. DIY Wire Antennas**
- Cut wire to quarter-wave
- Solder to SMA connector
- FREE but requires some skill

---

## Usage Workflow

### 1. Initial Setup
```bash
# Check your HackRFs are detected
python cli.py status

# You should see BOTH devices listed
```

### 2. Run Direction Finding Scan
```bash
# For a specific frequency (e.g., GSM 850 at 869 MHz)
python cli.py df-scan --freq 869000000 --spacing 0.18
```

**Output:**
```
Bearing: 127° (Southeast)
Direction: Southeast
Confidence: HIGH

Walk/drive toward Southeast (127°)
```

### 3. Navigate to Tower
- Use phone compass
- Walk in the indicated direction
- Repeat DF scan every 100m to refine bearing
- Signal strength increases as you get closer

### 4. Advanced: Combine with Triangulation
- Do DF scan from location A → Bearing 1
- Move 200m perpendicular
- Do DF scan from location B → Bearing 2
- Where the bearings cross = tower location!

---

## Calibration (Optional but Recommended)

Use a known signal source to calibrate:

### Example: FM Radio Station

1. Find a local FM station tower (check FCC database)
2. Stand at known distance/bearing from it
3. Run calibration:

```bash
python cli.py df-calibrate --freq 96500000 --bearing 45 --spacing 0.18
```

System will calculate offset and improve accuracy for all future scans.

---

## Tips for Best Results

### DO:
✅ Use identical antennas
✅ Keep them the same height
✅ Test in open areas first
✅ Point array perpendicular to suspected tower
✅ Take multiple measurements
✅ Use strong signals for calibration

### DON'T:
❌ Use different antenna types
❌ Scan indoors (multipath errors)
❌ Expect perfect accuracy (±15° is typical)
❌ Forget about 180° ambiguity (front/back)
❌ Use when signal is too weak

---

## Troubleshooting

### "Only one HackRF detected"
- Check both USB cables connected
- Verify in Device Manager (both devices visible?)
- Try different USB ports
- Install WinUSB driver for second HackRF

### "Low confidence"
- Signal too weak - get closer to tower
- Multipath interference - move outdoors
- Antennas not identical - match them
- Wrong antenna spacing - recalculate for frequency

### "Bearing doesn't make sense"
- Run calibration with known source
- Check antenna orientation
- Verify frequency is correct
- Try different spacing

---

## Example: Hunting a Rogue 5G Tower

**Detected tower:** 2512 MHz, -22 dBm (very strong)

**Step 1: Calculate spacing**
```
Spacing = 300,000,000 / (2,512,000,000 * 2) = 0.06m = 6cm
```

**Step 2: Mount antennas 6cm apart**

**Step 3: Run DF scan**
```bash
python cli.py df-scan --freq 2512000000 --spacing 0.06
```

**Step 4: Get bearing (e.g., 127° Southeast)**

**Step 5: Walk southeast using phone compass**

**Step 6: Repeat scan every 50-100m**

**Step 7: Bearing will change as you move - keep following it**

**Result:** Find the physical tower location! 🎯

---

## Ready to Hunt!

Your dual-HackRF Stingray Hunter is now a complete direction finding system!

**Commands:**
- `python cli.py scan` - Detect towers
- `python cli.py ai-hunt` - AI-guided hunting  
- `python cli.py df-scan --freq X` - Get bearing to tower
- `python cli.py triangulate TOWER_ID` - GPS triangulation

**You now have THREE ways to locate rogue towers:**
1. GPS triangulation (multiple scans + lat/lon)
2. Direction finding (dual HackRF + bearing)
3. Combined approach (best accuracy!)

Happy hunting! 🛰️🧭
