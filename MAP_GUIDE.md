# Google Maps Integration for Stingray Hunter

## Quick Start

### 1. Get a Google Maps API Key (FREE)

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable "Maps JavaScript API"
4. Create API key (under Credentials)
5. Copy your API key

### 2. Add Your API Key

Edit `tower_map.html` and replace `YOUR_API_KEY_HERE` with your actual key on line ~267:
```html
<script async defer
    src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_KEY&callback=initMap">
</script>
```

### 3. Open the Map

Simply open `tower_map.html` in your web browser!

**Or run:**
```bash
start tower_map.html
```

## How to Use

### Planning Scan Locations

1. **Find your area** - Map will try to auto-locate you
2. **Click 3 spots** around where you suspect a rogue tower
   - Spots should be ~100m apart
   - Form a triangle around the suspected tower location
3. **Copy coordinates** - Click each marker to get lat/lon
4. **Copy the command** - Click the command box to copy to clipboard

### Running Scans

Drive to each marked location and run:
```bash
python cli.py scan-locate --lat 37.774900 --lon -122.419400
```

Repeat for all 3 locations.

### View Triangulated Towers

After triangulating, run:
```bash
python generate_map.py
```

This creates `tower_map_generated.html` with your detected towers shown as red markers!

## Features

- 🗺️ **Click to get coordinates** - Interactive point selection
- 📋 **One-click copy** - Copy coordinates or commands
- 🎯 **Smart suggestions** - Auto-generate optimal scan points
- 📍 **Multiple markers** - Track all your scan locations
- 🚨 **Tower visualization** - See suspicious vs normal towers

## Keyboard Shortcuts

- Click map → Get coordinates
- Click command box → Copy command
- Click coordinate box → See details

## Tips

- Place your 3 scan points in a **triangle** around the target
- Keep points **100-200m apart** for best accuracy
- Scan from areas with **good line of sight** (outdoors, elevated)
- **Save your markers** by not refreshing the page

Enjoy hunting! 🛰️
