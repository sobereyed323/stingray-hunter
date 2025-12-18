"""
Generate HTML map with tower locations from database.
"""

import sqlite3
import json
from pathlib import Path


def generate_tower_map(db_path: Path, output_path: Path):
    """Generate an HTML map showing all detected towers."""
    
    # Read tower data from database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get triangulated towers (those with location measurements)
    cursor.execute("""
        SELECT DISTINCT t.unique_id, t.technology, t.frequency_mhz, 
               t.avg_signal, t.is_suspicious
        FROM towers t
        INNER JOIN location_measurements lm ON t.unique_id = lm.tower_id
    """)
    
    triangulated_towers = cursor.fetchall()
    
    # Get all location measurements
    cursor.execute("""
        SELECT tower_id, latitude, longitude, signal_strength
        FROM location_measurements
        ORDER BY timestamp DESC
    """)
    
    measurements = cursor.fetchall()
    conn.close()
    
    # Read the HTML template
    template_path = Path(__file__).parent.parent / 'tower_map.html'
    with open(template_path, 'r') as f:
        html = f.read()
    
    # Generate JavaScript to add tower markers
    js_code = "\n// Auto-generated tower markers\n"
    
    for tower_id, tech, freq, signal, suspicious in triangulated_towers:
        # Calculate average position from measurements
        tower_measurements = [m for m in measurements if m[0] == tower_id]
        if tower_measurements:
            avg_lat = sum(m[1] for m in tower_measurements) / len(tower_measurements)
            avg_lng = sum(m[2] for m in tower_measurements) / len(tower_measurements)
            
            js_code += f"addTowerMarker({avg_lat}, {avg_lng}, '{tower_id}', {str(bool(suspicious)).lower()});\n"
    
    # Insert the JavaScript before the closing script tag
    html = html.replace('// Example: Add a suspicious tower marker', js_code)
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Map generated: {output_path}")
    print(f"Added {len(triangulated_towers)} towers")


if __name__ == '__main__':
    import sys
    
    db_path = Path('data/towers.db')
    output_path = Path('tower_map_generated.html')
    
    if db_path.exists():
        generate_tower_map(db_path, output_path)
        print(f"\nOpen {output_path} in your browser to view the map!")
    else:
        print(f"Database not found: {db_path}")
        print("Run some scans first!")
