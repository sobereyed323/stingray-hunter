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
    """Show tower database report."""
    config = ctx.obj['config']
    db = TowerDatabase(config.database_path)
    
    stats = db.stats()
    
    console.print(Panel.fit("📊 [bold]Tower Database Report[/bold]", style="cyan"))
    
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Towers", str(stats['total_towers']))
    table.add_row("Baseline Towers", str(stats['baseline_towers']))
    table.add_row("Suspicious Towers", str(stats['suspicious_towers']))
    table.add_row("Total Sightings", str(stats['total_sightings']))
    
    console.print(table)
    
    # Show suspicious towers
    suspicious = db.get_suspicious_towers()
    if suspicious:
        console.print("\n[red bold]⚠️ Suspicious Towers:[/red bold]")
        for tower in suspicious:
            console.print(f"  • {tower.unique_id} - {tower.notes}")

if __name__ == '__main__':
    cli()
