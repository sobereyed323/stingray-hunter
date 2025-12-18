# HackRF One + PortaPack - Complete Use Cases Guide

Your HackRF One with PortaPack is a powerful SDR platform covering **1 MHz to 6 GHz**. Here's what you can do:

---

## 🎯 Security & Research

### 1. **Rogue Cell Tower Detection** (What we built!)
- Hunt IMSI catchers / Stingrays
- Baseline legitimate towers
- Detect anomalies in cellular signals

### 2. **Wireless Security Testing**
- WiFi spectrum analysis (2.4 GHz, 5 GHz)
- Bluetooth device discovery
- IoT device security testing
- Zigbee/Z-Wave analysis

### 3. **RF Signal Analysis**
- Identify unknown transmissions
- Reverse engineer protocols
- Analyze proprietary wireless systems

---

## 📡 Radio Reception

### 4. **Aircraft Tracking** 
- **ADS-B** (1090 MHz) - Track planes in real-time
- Use with software like `dump1090`
- See flight paths, altitudes, speeds

### 5. **Marine Tracking**
- **AIS** (162 MHz) - Track ships
- Ship positions, speeds, destinations

### 6. **Broadcast Radio**
- **FM Radio** (88-108 MHz)
- **AM Radio** (500-1700 kHz)
- **Shortwave** (3-30 MHz)
- **Weather Radio** (162 MHz)

### 7. **Amateur Radio**
- Listen to ham radio bands
- 2m (144-148 MHz), 70cm (420-450 MHz)
- Digital modes (APRS, FT8, etc.)

### 8. **Emergency Services** (Receive Only - Legal)
- Police/Fire/EMS (if unencrypted)
- Varies by location

---

## 🛰️ Satellite Communications

### 9. **Weather Satellites**
- **NOAA APT** (~137 MHz) - Weather images
- **Meteor M2** (137 MHz) - High-res weather
- Decode with software like WXtoImg

### 10. **ISS Communication**
- International Space Station (145.8 MHz)
- Hear astronaut voice transmissions

### 11. **GPS Signals**
- Analyze GPS L1 (1575 MHz)
- Study satellite positioning

---

## 🏠 Home Automation

### 12. **Smart Home Protocol Analysis**
- **433 MHz** - Garage doors, remotes, sensors
- **315 MHz** - Tire pressure monitors, car keys
- **868/915 MHz** - LoRa, ISM devices

### 13. **Decode Wireless Sensors**
- Weather stations
- Temperature sensors
- Door/window sensors

---

## 🚗 Automotive

### 14. **Car Key Fob Analysis** (Research Only!)
- Study rolling codes (315/433 MHz)
- Reverse engineer protocols
- **DO NOT use for unauthorized access**

### 15. **TPMS (Tire Pressure Monitoring)**
- Receive tire pressure sensor data (315/433 MHz)

---

## 📻 Transmit Capabilities (WITH LICENSE!)

> **⚠️ WARNING**: Transmitting requires proper amateur radio license in most countries!

### 16. **Ham Radio Transmission**
- 2m/70cm bands (with license)
- Digital modes, voice, CW

### 17. **Test Signal Generation**
- RF testing and calibration
- Frequency reference

---

## 🎓 Learning & Education

### 18. **SDR Learning**
- Understand modulation (AM, FM, SSB, QAM)
- Learn signal processing
- Study RF propagation

### 19. **Reverse Engineering**
- Capture and analyze unknown signals
- Decode proprietary protocols
- Security research

---

## 🔧 PortaPack-Specific Apps

Your PortaPack Mayhem firmware includes:

| App | Purpose |
|-----|---------|
| **Spectrum Analyzer** | Real-time frequency visualization |
| **Audio** | Listen to FM/AM signals |
| **ADS-B** | Track aircraft |
| **AFSK** | Decode AFSK modulation |
| **POCSAG** | Pager decoding |
| **TPMS** | Tire pressure sensors |
| **GPS Sim** | GPS signal simulation (testing only!) |
| **Replay** | Record and replay RF signals |
| **Scanner** | Frequency scanner |

---

## 📚 Popular Software (PC Mode)

When connected to PC, use these tools:

| Software | Use |
|----------|-----|
| **GNU Radio** | Visual signal processing |
| **SDR#** | General SDR receiver |
| **GQRX** | SDR receiver (Linux/Mac) |
| **Universal Radio Hacker** | Protocol analysis |
| **dump1090** | ADS-B aircraft tracking |
| **rtl_433** | 433 MHz device decoding |
| **inspectrum** | Signal analysis |

---

## ⚖️ Legal & Safety

**Legal to receive:**
- Broadcast radio (AM/FM/TV)
- Amateur radio
- Public safety (unencrypted)
- Aviation (ADS-B, VHF)
- Satellites
- ISM bands (433/868/915 MHz)

**Illegal/Restricted:**
- **Cellular calls** (privacy violation)
- **Encrypted communications** (illegal to decode)
- **Transmitting without license** (most bands)
- **Jamming** (highly illegal, felony)

**Golden Rule:** If you can buy it at a store and it uses radio, you can usually listen. Always check local laws!

---

## 🚀 Next Steps

**Want to try something?**
1. **Easy**: Listen to FM radio or weather satellites
2. **Medium**: Track aircraft with ADS-B
3. **Advanced**: Reverse engineer a 433 MHz garage door remote

Your HackRF is a complete radio lab in your hands! 🛰️
