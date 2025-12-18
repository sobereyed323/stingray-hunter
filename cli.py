#!/usr/bin/env python3
"""
Stingray Hunter CLI - Rogue Cell Tower Detection
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from datetime import datetime

from stingray_hunter.config import Config
from stingray_hunter.device_manager import DeviceManager, check_hackrf_available
from stingray_hunter.scanner import Scanner
from stingray_hunter.tower_db import TowerDatabase
from stingray_hunter.detector import AnomalyDetector, ThreatLevel
from stingray_hunter.alerts import AlertSystem

console = Console()

@click.group()
@click.pass_context
def cli(ctx):
    """🛰️ Stingray Hunter - Rogue Cell Tower Detection Toolkit"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config.default()

@cli.command()
def status():
    """Show HackRF device status."""
    console.print(Panel.fit("🛰️ [bold]Stingray Hunter[/bold] - Device Status", style="cyan"))
    
    if not check_hackrf_available():
        console.print("[red]❌ No HackRF devices detected![/red]")
        console.print("\nMake sure your HackRF is connected and drivers are installed.")
        return
    
    dm = DeviceManager()
    devices = dm.enumerate_devices()
    
    table = Table(title="Connected Devices")
    table.add_column("Index", style="cyan")
    table.add_column("Serial", style="green")
    table.add_column("PortaPack", style="yellow")
    table.add_column("Role", style="magenta")
    
    for device in devices:
        table.add_row(
            str(device.index),
            device.serial,
            "✅" if device.is_portapack else "❌",
            device.role.value
        )
    
    console.print(table)

@cli.command()
@click.option('--continuous', '-c', is_flag=True, help='Run continuous scan')
@click.pass_context
def scan(ctx, continuous):
    """Scan for cell towers."""
    config = ctx.obj['config']
    
    console.print(Panel.fit("🛰️ [bold]Cell Tower Scan[/bold]", style="cyan"))
    
    if not check_hackrf_available():
        console.print("[red]❌ No HackRF devices detected![/red]")
        return
    
    # Initialize components
    dm = DeviceManager()
    devices = dm.enumerate_devices()
    dm.assign_roles(auto=True)
    
    db = TowerDatabase(config.database_path)
    detector = AnomalyDetector(config, db)
    alerts = AlertSystem(console=True, sound=True, log_dir=config.scan_log_dir)
    
    scanner = Scanner(config, devices[0] if devices else None)
    
    console.print(f"[green]✓[/green] Using device: {devices[0] if devices else 'default'}")
    console.print(f"[green]✓[/green] Database: {config.database_path}")
    console.print("[yellow]Scanning...[/yellow]\n")
    
    try:
        if continuous:
            for towers in scanner.continuous_scan():
                _process_scan(towers, db, detector, alerts)
        else:
            towers = scanner.scan_all_bands()
            _process_scan(towers, db, detector, alerts)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan stopped.[/yellow]")

def _process_scan(towers, db, detector, alerts):
    """Process a single scan result."""
    console.print(f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] Found {len(towers)} towers")
    
    for tower in towers:
        db.record_tower(tower)
    
    anomalies = detector.analyze(towers)
    if anomalies:
        alerts.alert_all(anomalies)

@cli.command()
@click.pass_context
def baseline(ctx):
    """Mark all current towers as baseline (known good)."""
    config = ctx.obj['config']
    db = TowerDatabase(config.database_path)
    
    count = db.baseline_all_current()
    console.print(f"[green]✓[/green] Marked {count} towers as baseline")

@cli.command()
@click.pass_context
def report(ctx):
    """Show tower database summary."""
    config = ctx.obj['config']
    console.print("\n[bold cyan]╭──────────────────────────╮[/bold cyan]")
    console.print("[bold cyan]│ 📊 Tower Database Report │[/bold cyan]")
    console.print("[bold cyan]╰──────────────────────────╯[/bold cyan]\n")
    
    db = TowerDatabase(config.database_path) # Changed TowerDB() to TowerDatabase(config.database_path)
    stats = db.stats() # Changed get_statistics() to stats()
    
    table = Table(title=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Towers", str(stats['total_towers'])) # Changed 'total' to 'total_towers'
    table.add_row("Baseline Towers", str(stats['baseline_towers'])) # Changed 'baseline' to 'baseline_towers'
    table.add_row("Suspicious Towers", str(stats['suspicious_towers'])) # Changed 'suspicious' to 'suspicious_towers'
    table.add_row("Total Sightings", str(stats['total_sightings'])) # Changed 'sightings' to 'total_sightings'
    
    console.print(table)
    
    # Show suspicious towers
    suspicious = db.get_suspicious_towers()
    if suspicious:
        console.print("\n[bold yellow]⚠️ Suspicious Towers:[/bold yellow]")
        for tower in suspicious:
            console.print(f"  • {tower.unique_id} - {tower.notes}") # Changed tower['tower_id'] and tower['reason'] to tower.unique_id and tower.notes


@cli.command()
@click.pass_context
def detailed_report(ctx):
    """Generate detailed report of all detected towers."""
    config = ctx.obj['config']
    console.print("\n[bold cyan]╭────────────────────────────────────╮[/bold cyan]")
    console.print("[bold cyan]│ 📡 Detailed Cell Tower Report     │[/bold cyan]")
    console.print("[bold cyan]╰────────────────────────────────────╯[/bold cyan]\n")
    
    db = TowerDatabase(config.database_path) # Changed TowerDB() to TowerDatabase(config.database_path)
    
    # Get all towers grouped by technology
    import sqlite3
    conn = sqlite3.connect(config.database_path) # Changed 'data/towers.db' to config.database_path
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT technology, COUNT(*), AVG(avg_signal), 
               MIN(frequency_mhz), MAX(frequency_mhz)
        FROM towers
        GROUP BY technology
        ORDER BY technology
    """)
    
    tech_summary = cursor.fetchall()
    
    if tech_summary:
        console.print("[bold]Summary by Technology:[/bold]\n")
        summary_table = Table()
        summary_table.add_column("Technology", style="cyan")
        summary_table.add_column("Count", style="green")
        summary_table.add_column("Avg Signal", style="yellow")
        summary_table.add_column("Freq Range (MHz)", style="magenta")
        
        for tech, count, avg_signal, min_freq, max_freq in tech_summary:
            freq_range = f"{min_freq:.1f} - {max_freq:.1f}"
            summary_table.add_row(
                tech,
                str(count),
                f"{avg_signal:.1f} dBm",
                freq_range
            )
        
        console.print(summary_table)
    
    # Detailed tower list
    cursor.execute("""
        SELECT unique_id, frequency_mhz, avg_signal, technology, 
               first_seen, last_seen, times_seen, is_baseline, is_suspicious
        FROM towers
        ORDER BY technology, frequency_mhz
    """)
    
    towers = cursor.fetchall()
    
    if towers:
        console.print("\n[bold]Detailed Tower List:[/bold]\n")
        
        current_tech = None
        for tower in towers:
            tower_id, freq, signal, tech, first, last, count, baseline, suspicious = tower
            
            # Print technology header when it changes
            if tech != current_tech:
                console.print(f"\n[bold cyan]═══ {tech} Towers ═══[/bold cyan]")
                current_tech = tech
            
            # Status indicators
            status = []
            if baseline:
                status.append("[green]✓ Baseline[/green]")
            if suspicious:
                status.append("[red]⚠ Suspicious[/red]")
            
            status_str = " ".join(status) if status else "[dim]New[/dim]"
            
            console.print(
                f"  📡 [cyan]{tower_id}[/cyan]\n"
                f"     Frequency: {freq:.2f} MHz | Signal: {signal:.1f} dBm\n"
                f"     Status: {status_str} | Sightings: {count}\n"
                f"     First: {first} | Last: {last}"
            )
    else:
        console.print("[yellow]No towers in database yet.[/yellow]")
    
    conn.close()
    
    # Export option
    console.print("\n[dim]Tip: Data is stored in data/towers.db for further analysis[/dim]")


@cli.command()
@click.option('--lat', type=float, required=True, help='Latitude (decimal degrees)')
@click.option('--lon', type=float, required=True, help='Longitude (decimal degrees)')
@click.option('--continuous', '-c', is_flag=True, help='Run continuous scan')
@click.pass_context
def scan_locate(ctx, lat, lon, continuous):
    """Scan for towers with GPS location tagging for triangulation."""
    config = ctx.obj['config']
    
    from stingray_hunter.gps import GPSCoordinate
    
    # Validate GPS coordinates
    try:
        location = GPSCoordinate(lat, lon)
    except ValueError as e:
        console.print(f"[red]Invalid GPS coordinates: {e}[/red]")
        return
    
    console.print(Panel.fit(f"🛰️ [bold]Location-Tagged Scan[/bold]", style="cyan"))
    console.print(f"📍 Location: {location}")
    
    if not check_hackrf_available():
        console.print("[red]❌ No HackRF devices detected![/red]")
        return
    
    # Initialize components
    dm = DeviceManager()
    devices = dm.enumerate_devices()
    dm.assign_roles(auto=True)
    
    db = TowerDatabase(config.database_path)
    detector = AnomalyDetector(config, db)
    alerts = AlertSystem(console=True, sound=False, log_dir=config.scan_log_dir)
    scanner = Scanner(config, devices[0] if devices else None)
    
    console.print(f"[green]✓[/green] Using device: {devices[0] if devices else 'default'}")
    console.print(f"[green]✓[/green] GPS: {location}")
    console.print("[yellow]Scanning...[/yellow]\n")
    
    # Generate scan ID for this location
    from datetime import datetime
    scan_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        towers = scanner.scan_all_bands()
        count = len(towers)
        console.print(f"[green]✓[/green] Found {count} towers at this location\n")
        
        # Record towers and location measurements
        for tower in towers:
            db.record_tower(tower)
            db.record_location_measurement(
                tower.unique_id,
                location.latitude,
                location.longitude,
                tower.signal_strength,
                scan_id
            )
        
        # Run anomaly detection
        anomalies = detector.analyze(towers)
        if anomalies:
            alerts.alert_all(anomalies)
        
        console.print(f"\n[dim]Scan ID: {scan_id}[/dim]")
        console.print("[green]Location measurements saved for triangulation[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan stopped.[/yellow]")


@cli.command()
@click.argument('tower_id')
@click.pass_context
def triangulate(ctx, tower_id):
    """Triangulate the location of a tower using recorded measurements."""
    config = ctx.obj['config']
    
    from stingray_hunter.gps import GPSCoordinate, google_maps_url
    from stingray_hunter.triangulate import Triangulator, Measurement
    
    console.print(Panel.fit(f"📍 [bold]Tower Triangulation[/bold]", style="cyan"))
    console.print(f"Analyzing tower: [cyan]{tower_id}[/cyan]\n")
    
    db = TowerDatabase(config.database_path)
    
    # Get location measurements for this tower
    measurements_data = db.get_location_measurements(tower_id)
    
    if not measurements_data:
        console.print(f"[red]No location measurements found for tower {tower_id}[/red]")
        console.print("\nRun [cyan]scan-locate --lat LAT --lon LON[/cyan] at multiple locations first")
        return
    
    console.print(f"Found {len(measurements_data)} measurement(s)\n")
    
    if len(measurements_data) < 3:
        console.print(f"[yellow]⚠ Need at least 3 measurements from different locations[/yellow]")
        console.print(f"[yellow]  Currently have: {len(measurements_data)}[/yellow]")
        console.print("\nTake more scans at different locations using:")
        console.print("[cyan]  scan-locate --lat LAT --lon LON[/cyan]\n")
    
    # Convert to Measurement objects
    from datetime import datetime
    measurements = []
    for m in measurements_data:
        location = GPSCoordinate(m['latitude'], m['longitude'])
        measurement = Measurement(
            location=location,
            signal_dbm=m['signal_strength'],
            tower_id=m['tower_id'],
            timestamp=m['timestamp']
        )
        measurements.append(measurement)
    
    # Display measurements
    table = Table(title="Measurements")
    table.add_column("#", style="cyan")
    table.add_column("Location", style="green")
    table.add_column("Signal", style="yellow")
    table.add_column("Timestamp", style="dim")
    
    for i, m in enumerate(measurements, 1):
        table.add_row(
            str(i),
            str(m.location),
            f"{m.signal_dbm:.1f} dBm",
            m.timestamp
        )
    
    console.print(table)
    
    # Perform triangulation
    if len(measurements) >= 3:
        triangulator = Triangulator(path_loss_exponent=3.0)
        result = triangulator.trilaterate(measurements)
        
        if result:
            est_location, accuracy = result
            
            console.print(f"\n[bold green]Estimated Tower Location:[/bold green]")
            console.print(f"  Latitude:  {est_location.latitude:.6f}°")
            console.print(f"  Longitude: {est_location.longitude:.6f}°")
            console.print(f"  Accuracy:  ±{accuracy:.0f} meters\n")
            
            maps_url = google_maps_url(est_location)
            console.print(f"[cyan]Google Maps:[/cyan] {maps_url}")
            console.print(f"[dim]Copy/paste the URL above to view in a browser[/dim]")
        else:
            console.print("[red]Triangulation failed[/red]")
    else:
        # Show diagnostics for partial data
        triangulator = Triangulator()
        analysis = triangulator.analyze_measurements(measurements)
        
        console.print("\n[bold]Measurement Analysis:[/bold]")
        console.print(f"  Signal range: {analysis['min_signal']:.1f} to {analysis['max_signal']:.1f} dBm")
        console.print(f"  Average:      {analysis['avg_signal']:.1f} dBm")
        
        if 'estimated_distances' in analysis:
            console.print(f"\n[bold]Estimated distances from measurement points:[/bold]")
            for i, dist in enumerate(analysis['estimated_distances'], 1):
                console.print(f"  Point {i}: ~{dist:.0f} meters")


@cli.command()
@click.option('--lat', type=float, help='Your current latitude (optional)')
@click.option('--lon', type=float, help='Your current longitude (optional)')
@click.pass_context
def ai_hunt(ctx, lat, lon):
    """🤖 AI-guided tower hunting - Let the AI plan and guide your hunt!"""
    config = ctx.obj['config']
    
    from stingray_hunter.ai_analyzer import AIAnalyzer
    from stingray_hunter.gps import GPSCoordinate, google_maps_url
    
    console.print(Panel.fit("🤖 [bold]AI-Guided Tower Hunt[/bold]", style="cyan"))
    
    db = TowerDatabase(config.database_path)
    ai = AIAnalyzer(db)
    
    # Get user location if provided
    user_location = None
    if lat and lon:
        try:
            user_location = GPSCoordinate(lat, lon)
            console.print(f"📍 Your location: {user_location}\n")
        except ValueError as e:
            console.print(f"[red]Invalid coordinates: {e}[/red]")
            return
    
    # Step 1: Identify top threat
    console.print("[bold]Step 1: Identifying Top Threat[/bold]")
    console.print("[dim]Analyzing all detected towers...[/dim]\n")
    
    target = ai.identify_top_threat()
    
    if not target:
        console.print("[yellow]No suspicious towers detected yet![/yellow]")
        console.print("\nRun [cyan]scan[/cyan] first to detect towers in your area")
        return
    
    console.print(f"[bold red]🎯 Target Identified:[/bold red]")
    console.print(f"  Tower ID: [cyan]{target.unique_id}[/cyan]")
    console.print(f"  Technology: {target.technology}")
    console.print(f"  Frequency: {target.frequency_mhz:.2f} MHz")
    console.print(f"  Signal: {target.avg_signal:.1f} dBm")
    
    # Step 2: Create hunting plan
    console.print(f"\n[bold]Step 2: Creating Hunting Plan[/bold]")
    console.print("[dim]AI is calculating optimal scan locations...[/dim]\n")
    
    plan = ai.create_hunting_plan(target, user_location)
    
    # Display threat level
    threat_colors = {
        'HIGH': 'red',
        'MEDIUM': 'yellow',
        'LOW': 'green'
    }
    
    color = threat_colors.get(plan.threat_level, 'white')
    console.print(f"[bold {color}]Threat Level: {plan.threat_level}[/bold {color}]\n")
    
    # Display analysis
    console.print("[bold]AI Analysis:[/bold]")
    for line in plan.analysis.split('\n'):
        console.print(f"  {line}")
    
    # Display scan points
    console.print(f"\n[bold cyan]Recommended Scan Points:[/bold cyan]")
    
    if plan.scan_points[0].location.latitude == 0:
        console.print("[yellow]⚠ No location data available[/yellow]")
        console.print("\nTo get started:")
        console.print("1. Go to your current location")
        console.print("2. Run: [cyan]scan-locate --lat YOUR_LAT --lon YOUR_LON[/cyan]")
        console.print("3. Run [cyan]ai-hunt[/cyan] again for updated recommendations")
        return
    
    table = Table()
    table.add_column("#", style="cyan", width=3)
    table.add_column("GPS Coordinates", style="green")
    table.add_column("Distance", style="yellow")
    table.add_column("Command", style="dim", overflow="fold")
    
    for point in plan.scan_points:
        cmd = f"scan-locate --lat {point.location.latitude:.6f} --lon {point.location.longitude:.6f}"
        table.add_row(
            str(point.priority),
            f"{point.location.latitude:.6f}, {point.location.longitude:.6f}",
            f"~{point.distance_from_center:.0f}m",
            cmd
        )
    
    console.print(table)
    
    # Show on Google Maps
    if plan.estimated_location:
        maps_url = google_maps_url(plan.estimated_location)
        console.print(f"\n[cyan]📍 Estimated Tower Location:[/cyan]")
        console.print(f"  {maps_url}")
    
    # Quality assessment if we have measurements
    measurements = db.get_location_measurements(target.unique_id)
    if measurements:
        quality = ai.analyze_triangulation_quality(measurements)
        
        quality_colors = {
            'EXCELLENT': 'green',
            'GOOD': 'yellow',
            'POOR': 'red',
            'INSUFFICIENT': 'dim'
        }
        
        q_color = quality_colors.get(quality['quality'], 'white')
        console.print(f"\n[bold]Data Quality: [{q_color}]{quality['quality']}[/{q_color}][/bold]")
        console.print(f"  Confidence: {quality['confidence']}%")
        console.print(f"  {quality['recommendation']}")
    
    # Step 3: Next steps
    console.print(f"\n[bold green]Your Mission:[/bold green]")
    for step in plan.next_steps:
        console.print(f"  {step}")
    
    # Helpful tips
    console.print(f"\n[dim]💡 Tips:[/dim]")
    console.print(f"[dim]• Drive to each point and run the command shown[/dim]")
    console.print(f"[dim]• Scans take ~3 minutes each[/dim]")
    console.print(f"[dim]• After 3 scans, run 'ai-hunt' again for results[/dim]")
    console.print(f"[dim]• View points on Google Maps using the URL above[/dim]")


@cli.command()
@click.option('--freq', type=float, required=True, help='Frequency in Hz (e.g., 869000000)')
@click.option('--spacing', type=float, default=0.18, help='Antenna spacing in meters (default: 0.18m for GSM 850)')
@click.option('--device1', type=int, default=0, help='First HackRF device index')
@click.option('--device2', type=int, default=1, help='Second HackRF device index')
@click.pass_context
def df_scan(ctx, freq, spacing, device1, device2):
    """🧭 Direction Finding - Get bearing to signal source using dual HackRFs."""
    from stingray_hunter.direction_finding import DirectionFinder
    from stingray_hunter.dual_receiver import DualReceiver
    
    console.print(Panel.fit("🧭 [bold]Direction Finding Scan[/bold]", style="cyan"))
    console.print(f"Frequency: {freq/1e6:.2f} MHz")
    console.print(f"Antenna spacing: {spacing*100:.1f} cm\n")
    
    # Initialize DF components
    df = DirectionFinder(antenna_spacing_m=spacing)
    receiver = DualReceiver()
    
    # Check both devices are available
    console.print("[dim]Checking HackRF devices...[/dim]")
    if not receiver.check_device_available(device1):
        console.print(f"[red]✗ HackRF device {device1} not available[/red]")
        return
    console.print(f"[green]✓ HackRF #{device1} ready[/green]")
    
    if not receiver.check_device_available(device2):
        console.print(f"[red]✗ HackRF device {device2} not available[/red]")
        console.print("\n[yellow]Only one HackRF detected. Need two for direction finding.[/yellow]")
        console.print("[dim]Make sure both HackRFs are connected and have drivers installed.[/dim]")
        return
    console.print(f"[green]✓ HackRF #{device2} ready[/green]\n")
    
    # Capture IQ samples from both receivers
    console.print("[yellow]Capturing samples from both receivers...[/yellow]")
    console.print("[dim]This may take 10-15 seconds...[/dim]\n")
    
    with console.status("[bold green]Sampling...") as status:
        samples1, samples2 = receiver.capture_dual_samples(
            frequency_hz=freq,
            sample_rate_hz=2000000,
            num_samples=2000000,
            device1_index=device1,
            device2_index=device2
        )
    
    if samples1 is None or samples2 is None:
        console.print("[red]✗ Failed to capture samples from one or both receivers[/red]")
        console.print("[dim]Check that both HackRFs are properly connected[/dim]")
        return
    
    console.print(f"[green]✓[/green] Captured {len(samples1)} samples from receiver 1")
    console.print(f"[green]✓[/green] Captured {len(samples2)} samples from receiver 2\n")
    
    # Estimate signal strength
    signal_strength = receiver.estimate_signal_strength(samples1)
    
    # Calculate bearing
    console.print("[yellow]Calculating bearing...[/yellow]")
    result = df.calculate_bearing(samples1, samples2, freq, signal_strength)
    
    # Display results
    console.print(f"\n[bold green]═══ Direction Finding Result ═══[/bold green]\n")
    
    console.print(f"[bold cyan]Bearing: {result.bearing_degrees:.1f}°[/bold cyan]")
    
    # Show compass direction
    _, cardinal = df.bearing_to_compass(result.bearing_degrees)
    console.print(f"Direction: [bold]{cardinal}[/bold]")
    
    console.print(f"Signal Strength: {result.signal_strength_dbm:.1f} dBm")
    console.print(f"Confidence: [{'green' if result.confidence == 'HIGH' else 'yellow' if result.confidence == 'MEDIUM' else 'red'}]{result.confidence}[/]")
    
    if result.ambiguity_warning:
        console.print(f"\n[yellow]⚠ 180° ambiguity:[/yellow] Signal could be from {result.bearing_degrees:.1f}° OR {(result.bearing_degrees + 180) % 360:.1f}°")
        console.print("[dim]Take another measurement from a different location to resolve ambiguity[/dim]")
    
    console.print(f"\n[dim]Phase difference: {result.phase_difference_rad:.3f} rad[/dim]")
    
    # Provide guidance
    console.print(f"\n[bold]Next Steps:[/bold]")
    console.print(f"  • Walk/drive toward {cardinal} ({result.bearing_degrees:.0f}°)")
    console.print(f"  • Use compass or phone GPS navigation")
    console.print(f"  • Take another DF scan from new location to triangulate")


@cli.command()
@click.option('--freq', type=float, required=True, help='Frequency in Hz')
@click.option('--bearing', type=float, required=True, help='Known bearing to signal source (degrees)')
@click.option('--spacing', type=float, default=0.18, help='Antenna spacing in meters')
@click.pass_context
def df_calibrate(ctx, freq, bearing, spacing):
    """🎯 Calibrate direction finder using a known signal source."""
    from stingray_hunter.direction_finding import DirectionFinder
    from stingray_hunter.dual_receiver import DualReceiver
    
    console.print(Panel.fit("🎯 [bold]DF Calibration[/bold]", style="cyan"))
    console.print(f"Known bearing: {bearing:.1f}°")
    console.print(f"Frequency: {freq/1e6:.2f} MHz\n")
    
    # Initialize components
    df = DirectionFinder(antenna_spacing_m=spacing)
    receiver = DualReceiver()
    
    # Capture and measure
    console.print("[yellow]Measuring current bearing...[/yellow]")
    
    samples1, samples2 = receiver.capture_dual_samples(freq)
    
    if samples1 is None or samples2 is None:
        console.print("[red]Calibration failed - could not capture samples[/red]")
        return
    
    signal_strength = receiver.estimate_signal_strength(samples1)
    result = df.calculate_bearing(samples1, samples2, freq, signal_strength)
    
    measured_bearing = result.bearing_degrees
    
    console.print(f"Measured bearing: {measured_bearing:.1f}°")
    console.print(f"Actual bearing: {bearing:.1f}°")
    
    # Calculate offset
    offset = df.calibrate(measured_bearing, bearing)
    
    console.print(f"\n[bold green]✓ Calibration offset: {offset:.1f}°[/bold green]")
    console.print(f"\n[dim]This offset will be applied to future DF scans[/dim]")
    console.print(f"[dim]Save this value in your config: --calibration {offset:.1f}[/dim]")


if __name__ == '__main__':
    cli()


