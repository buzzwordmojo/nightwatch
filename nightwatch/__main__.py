"""
Nightwatch entry point.

Run with: python -m nightwatch
Or: nightwatch (if installed)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

from nightwatch import __version__
from nightwatch.core.config import Config
from nightwatch.core.events import EventBus
from nightwatch.core.engine import AlertEngine
from nightwatch.core.notifiers.audio import AudioNotifier
from nightwatch.detectors.radar import RadarDetector
from nightwatch.detectors.radar.detector import MockRadarDetector
from nightwatch.detectors.audio.detector import MockAudioDetector
from nightwatch.detectors.bcg.detector import MockBCGDetector
from nightwatch.dashboard.server import DashboardServer
from nightwatch.bridge.convex import ConvexBridge, ConvexEventHandler
from nightwatch.setup.portal import CaptivePortal
from nightwatch.setup.hotspot import HotspotManager
from nightwatch.setup.first_boot import detect_setup_state, SetupState


async def run_setup_portal(
    config: Config,
    dev_mode: bool = False,
    setup_only: bool = False,
) -> None:
    """Run the setup portal for initial device configuration.

    Starts the captive portal (for WiFi setup), the dashboard server
    (for /api/setup/* endpoints), and optionally the hotspot (production only).

    Args:
        config: Nightwatch configuration
        dev_mode: If True, use mock WiFi data and skip hardware
        setup_only: If True, exit after setup completes (don't start monitoring)
    """
    print(f"🌙 Nightwatch Setup v{__version__}")
    print("=" * 40)

    if dev_mode:
        print("📁 Development mode: using mock WiFi data")

    # Check current state
    state = detect_setup_state()
    print(f"📊 Current state: {state.name}")

    if state == SetupState.FULLY_CONFIGURED and not setup_only:
        print("✅ Already configured! Starting monitoring...")
        return

    # Track components for cleanup
    hotspot = None
    dashboard = None
    portal = None

    # Setup completion event
    setup_complete = asyncio.Event()
    wifi_configured = asyncio.Event()

    async def on_wifi_configured(ssid: str):
        print(f"✅ WiFi configured: {ssid}")
        # Stop hotspot so device joins the real WiFi network
        if hotspot and hotspot.is_running:
            print("📡 Stopping hotspot for WiFi reconnect...")
            await hotspot.stop()
            await asyncio.sleep(3)  # Allow time for WiFi reconnect
        wifi_configured.set()

    try:
        # 1. Start hotspot (production only)
        if not dev_mode:
            hotspot = HotspotManager()
            print("📡 Starting WiFi hotspot...")
            await hotspot.start()
            print(f"📡 Hotspot active: {hotspot.ssid}")

        # 2. Start dashboard server (always — serves /api/setup/* endpoints)
        dashboard = DashboardServer(
            config=config.dashboard,
            mock_mode=dev_mode,
        )
        await dashboard.start()
        print(f"📊 Dashboard running at http://localhost:{config.dashboard.port}")

        # 3. Start captive portal
        portal = CaptivePortal(
            host="0.0.0.0",
            port=9532 if dev_mode else 80,
            gateway_ip="127.0.0.1" if dev_mode else "192.168.4.1",
            dashboard_url=f"http://localhost:{config.dashboard.port}/setup" if dev_mode else "http://nightwatch.local:9530/setup",
            on_wifi_configured=on_wifi_configured,
        )

        # In dev mode, patch the save function to use temp directory
        if dev_mode:
            import tempfile
            temp_dir = Path(tempfile.mkdtemp(prefix="nightwatch-"))
            print(f"📁 Config will be saved to: {temp_dir}")

            async def mock_save(credentials):
                config_file = temp_dir / "wifi.conf"
                config_file.write_text(f"ssid={credentials.ssid}\npassword={credentials.password}\n")
                print(f"📝 Saved credentials to {config_file}")

            portal._save_wifi_credentials = mock_save

        await portal.start()

        port = 9532 if dev_mode else 80
        print(f"🌐 Setup portal running at http://localhost:{port}/setup")
        print()
        print("Press Ctrl+C to stop")
        print()

        # Handle shutdown
        shutdown_event = asyncio.Event()

        def signal_handler():
            print("\n🛑 Shutting down...")
            shutdown_event.set()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        # 4. Poll for setup completion after WiFi is configured
        async def poll_setup_completion():
            """Wait for WiFi, then poll detect_setup_state until FULLY_CONFIGURED."""
            await wifi_configured.wait()
            print("⏳ Waiting for setup completion...")
            while True:
                state = detect_setup_state()
                if state == SetupState.FULLY_CONFIGURED:
                    print("✅ Setup complete!")
                    setup_complete.set()
                    return
                await asyncio.sleep(2)

        poll_task = asyncio.create_task(poll_setup_completion())

        # Wait for shutdown or setup completion
        wait_tasks = [
            asyncio.create_task(shutdown_event.wait()),
            asyncio.create_task(setup_complete.wait()),
        ]

        done, pending = await asyncio.wait(
            wait_tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel pending tasks
        poll_task.cancel()
        for task in pending:
            task.cancel()
        for task in [poll_task, *pending]:
            try:
                await task
            except asyncio.CancelledError:
                pass

    finally:
        # Cleanup all components
        if portal:
            await portal.stop()
        if dashboard:
            await dashboard.stop()
        if hotspot and hotspot.is_running:
            await hotspot.stop()

    print("👋 Setup portal stopped")


async def run_nightwatch(
    config: Config,
    mock_sensors: bool = False,
    enable_dashboard: bool = True,
    enable_convex: bool = False,
) -> None:
    """Run the Nightwatch monitoring system."""
    print(f"🌙 Starting Nightwatch v{__version__}")
    print("=" * 40)

    # Auto-detect setup state — run setup if not fully configured
    state = detect_setup_state()
    if state != SetupState.FULLY_CONFIGURED:
        print(f"📊 Setup state: {state.name} — entering setup mode")
        await run_setup_portal(config, dev_mode=mock_sensors)
        # Re-check after setup returns
        state = detect_setup_state()
        if state != SetupState.FULLY_CONFIGURED:
            print("❌ Setup not completed. Exiting.")
            return
        print("✅ Setup complete, starting monitoring...")

    # Create event bus
    event_bus = EventBus(
        event_endpoint=config.event_system.event_endpoint,
        alert_endpoint=config.event_system.alert_endpoint,
    )

    # Create notifiers
    notifiers = []
    if config.notifiers.audio.enabled:
        notifiers.append(AudioNotifier(config.notifiers.audio))

    # Create alert engine
    engine = AlertEngine(
        config=config.alert_engine,
        event_bus=event_bus,
        notifiers=notifiers,
    )

    # Create detectors
    detectors = []
    publisher = event_bus.create_publisher()

    if mock_sensors:
        print("📡 Using mock sensors for development")

        if config.detectors.radar.enabled:
            detectors.append(MockRadarDetector(publisher=publisher))
            print("  ✓ Mock radar detector")

        if config.detectors.audio.enabled:
            detectors.append(MockAudioDetector(publisher=publisher))
            print("  ✓ Mock audio detector")

        if config.detectors.bcg.enabled:
            detectors.append(MockBCGDetector(publisher=publisher))
            print("  ✓ Mock BCG detector")
    else:
        if config.detectors.radar.enabled:
            detectors.append(RadarDetector(
                config=config.detectors.radar,
                publisher=publisher,
            ))
            print("  ✓ Radar detector")

        # Real audio and BCG detectors would go here when hardware is connected
        # For now, fall back to mock if enabled but no hardware
        if config.detectors.audio.enabled:
            print("  ⚠ Audio detector (mock - no hardware)")
            detectors.append(MockAudioDetector(publisher=publisher))

        if config.detectors.bcg.enabled:
            print("  ⚠ BCG detector (mock - no hardware)")
            detectors.append(MockBCGDetector(publisher=publisher))

    if not detectors:
        print("❌ No detectors enabled! Check configuration.")
        sys.exit(1)

    # Create dashboard server
    dashboard = None
    if enable_dashboard:
        # Build detector dict for simulator control
        detector_dict = {}
        for d in detectors:
            detector_dict[d.name] = d

        dashboard = DashboardServer(
            config=config.dashboard,
            detectors=detector_dict,
            mock_mode=mock_sensors,
        )
        print(f"📊 Dashboard enabled at http://{config.dashboard.host}:{config.dashboard.port}")
        if mock_sensors:
            print(f"🎛️  Simulator available at http://{config.dashboard.host}:{config.dashboard.port}/sim")

    # Create Convex bridge (optional)
    convex_bridge = None
    convex_handler = None
    if enable_convex:
        convex_bridge = ConvexBridge()
        convex_handler = ConvexEventHandler(convex_bridge)
        print("🔗 Convex bridge enabled")

    # Wire up event handling
    async def on_event(event):
        await engine.process_event(event)

        if dashboard:
            dashboard.process_event(event)

        if convex_handler:
            await convex_handler(event)

    for detector in detectors:
        detector.set_on_event(on_event)

    # Handle shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        print("\n🛑 Shutting down...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Start components
    await engine.start()

    if dashboard:
        await dashboard.start()

    if convex_bridge:
        await convex_bridge.start()

    for detector in detectors:
        await detector.start()

    print("=" * 40)
    print(f"✅ Monitoring started with {len(detectors)} detector(s)")
    print("Press Ctrl+C to stop")
    print()

    # Wait for shutdown
    await shutdown_event.wait()

    # Cleanup
    for detector in detectors:
        await detector.stop()

    if dashboard:
        await dashboard.stop()

    if convex_bridge:
        await convex_bridge.stop()

    await engine.stop()
    await event_bus.close()

    print("👋 Shutdown complete")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="nightwatch",
        description="Open-source epilepsy monitoring system",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=None,
        help="Configuration file path",
    )
    parser.add_argument(
        "--mock-sensors",
        action="store_true",
        help="Use mock sensors for development/testing",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable the built-in dashboard server",
    )
    parser.add_argument(
        "--convex",
        action="store_true",
        help="Enable Convex bridge for Next.js dashboard",
    )
    parser.add_argument(
        "--simulate",
        type=Path,
        metavar="FILE",
        help="Run simulation from recording file",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Run predefined test scenario",
    )
    parser.add_argument(
        "--force-setup",
        action="store_true",
        help="Force setup mode (skip state detection, run setup wizard)",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Run only the setup portal (no monitoring)",
    )

    args = parser.parse_args()

    # Check for mock sensors via environment variable
    mock_sensors = args.mock_sensors or os.environ.get("NIGHTWATCH_MOCK", "").lower() in ("1", "true", "yes")

    # Find configuration file
    config_paths = [
        args.config,
        Path("config/default.yaml"),
        Path("/etc/nightwatch/config.yaml"),
        Path.home() / ".config/nightwatch/config.yaml",
    ]

    config = None
    for path in config_paths:
        if path and path.exists():
            print(f"Loading config from: {path}")
            config = Config.load(path)
            break

    if config is None:
        print("No config file found, using defaults")
        config = Config.default()

    # Validate config
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Check for setup mode
    force_setup = args.force_setup or os.environ.get("NIGHTWATCH_FORCE_SETUP", "").lower() in ("1", "true", "yes")
    setup_only = args.setup_only

    if force_setup or setup_only:
        # Run setup portal instead of monitoring
        asyncio.run(run_setup_portal(
            config,
            dev_mode=mock_sensors,
            setup_only=setup_only,
        ))
        return

    # Run
    try:
        asyncio.run(run_nightwatch(
            config,
            mock_sensors=mock_sensors,
            enable_dashboard=not args.no_dashboard,
            enable_convex=args.convex,
        ))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
