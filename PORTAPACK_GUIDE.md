# PortaPack H2 - Rogue Cell Tower Hunting Guide

## 🛰️ Quick Start

Your PortaPack has everything you need built-in!

---

## Step 1: Switch to PortaPack Mode

1. **Unplug HackRF** from computer
2. **Press the power button** on PortaPack (or it auto-starts)
3. You should see the **PortaPack Mayhem menu**

---

## Step 2: Using Spectrum Analyzer

**Best for finding strong signals (potential towers)**

1. From main menu → **Spectrum Analyzer**
2. Set frequency range:
   - **Press Center Freq** → Enter `869` (for 869 MHz GSM 850)
   - **Press Span** → Enter `25` (25 MHz wide)
3. **Look for strong vertical spikes** = cell towers
4. Note the frequencies where you see peaks

**Other bands to check:**
- `869-894 MHz` - GSM 850 / LTE Band 5
- `1930-1990 MHz` - GSM 1900 / LTE Band 2

---

## Step 3: Using Scanner App (Advanced)

1. Main menu → **Scanner**
2. Add frequencies manually or use presets
3. It will stop on active channels
4. Record strong signals

---

## Step 4: Baseline Your Area

**Do this first in a safe location like your home:**

1. Run spectrum analyzer on all cellular bands
2. **Take photos** of the screen showing normal tower signals
3. Note the frequencies and signal strengths

**These are your "known good" towers**

---

## Step 5: Hunt for Rogues

When you're out and about:

1. Run spectrum analyzer again
2. **Compare to your baseline photos**
3. **RED FLAGS:**
   - **New strong signal** (not in baseline)
   - **Signal much stronger** than at home
   - **Unusual frequency** not used by carriers

---

## 🎯 What to Look For

| Sign | What It Means |
|------|---------------|
| New peak at 869-894 MHz | Possible GSM tower |
| Very strong signal (>-30 dBm) | Tower very close (suspicious if mobile) |
| Signal follows you | BIG RED FLAG - possible IMSI catcher |

---

## 📱 Bonus: Antenna Tips

- Use the **ANT port** (not the AUX)
- For 850 MHz: 8-inch antenna works
- For 1900 MHz: 3-inch antenna works
- Higher elevation = better reception

---

## ⚠️ Troubleshooting

**Screen won't turn on?**
- Charge the PortaPack battery
- Check power switch

**No signals showing?**
- Check antenna is connected
- Try near a window
- Increase gain settings in spectrum analyzer

---

**That's it! Your PortaPack is a standalone rogue tower detector!** 🛰️
