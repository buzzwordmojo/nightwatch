"""
Captive portal server for Nightwatch setup.

Serves a minimal web interface for WiFi configuration during initial setup.
Handles Android and iOS captive portal detection automatically.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pydantic
from pydantic import BaseModel, Field
import uvicorn

logger = logging.getLogger(__name__)

# Paths
STATIC_DIR = Path(__file__).parent / "wizard" / "static"
TEMPLATES_DIR = Path(__file__).parent / "wizard" / "templates"


class WiFiCredentials(BaseModel):
    """WiFi network credentials."""

    ssid: str = Field(min_length=1)
    password: str  # Empty password allowed for open networks


class MonitorName(BaseModel):
    """Monitor name configuration."""

    name: str


class SetupProgress(BaseModel):
    """Current setup progress state."""

    step: int
    total_steps: int
    current_step_name: str
    wifi_configured: bool
    name_configured: bool


@dataclass
class CaptivePortal:
    """
    Captive portal server for initial device setup.

    Serves a minimal WiFi configuration page and handles
    platform-specific captive portal detection.
    """

    host: str = "0.0.0.0"
    port: int = 80
    gateway_ip: str = "192.168.4.1"
    dashboard_url: str = "http://nightwatch.local:3000/setup"
    on_wifi_configured: Any | None = None  # Callback when WiFi is set

    _app: FastAPI = field(default=None, init=False)  # type: ignore
    _server: uvicorn.Server | None = field(default=None, init=False)
    _wifi_credentials: WiFiCredentials | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="Nightwatch Setup",
            docs_url=None,
            redoc_url=None,
        )

        # ====================================================================
        # Captive Portal Detection Endpoints
        # ====================================================================

        @app.get("/generate_204")
        async def android_captive_check() -> Response:
            """Android captive portal detection - redirect to setup."""
            return RedirectResponse(
                url=f"http://{self.gateway_ip}/setup",
                status_code=302,
            )

        @app.get("/hotspot-detect.html")
        async def ios_captive_check() -> HTMLResponse:
            """iOS captive portal detection - must return specific HTML."""
            # iOS expects this to NOT return "Success" if captive
            return HTMLResponse(
                content=self._get_ios_captive_html(),
                status_code=200,
            )

        @app.get("/connectivitycheck.gstatic.com/generate_204")
        async def android_connectivity_check() -> Response:
            """Alternate Android captive portal detection."""
            return RedirectResponse(
                url=f"http://{self.gateway_ip}/setup",
                status_code=302,
            )

        @app.get("/captive.apple.com/hotspot-detect.html")
        async def apple_hotspot_detect() -> HTMLResponse:
            """Apple captive portal detection endpoint."""
            return HTMLResponse(
                content=self._get_ios_captive_html(),
                status_code=200,
            )

        @app.get("/www.msftconnecttest.com/connecttest.txt")
        async def windows_captive_check() -> Response:
            """Windows captive portal detection."""
            return RedirectResponse(
                url=f"http://{self.gateway_ip}/setup",
                status_code=302,
            )

        # ====================================================================
        # Setup Wizard Endpoints
        # ====================================================================

        @app.get("/")
        async def root() -> RedirectResponse:
            """Redirect root to setup page."""
            return RedirectResponse(url="/setup")

        @app.get("/setup", response_class=HTMLResponse)
        async def setup_page() -> HTMLResponse:
            """Serve the main setup wizard page."""
            return HTMLResponse(content=self._get_setup_html())

        @app.get("/api/setup/wifi/scan")
        async def scan_wifi_networks() -> JSONResponse:
            """Scan for available WiFi networks."""
            networks = await self._scan_wifi()
            return JSONResponse(content={"networks": networks})

        @app.post("/api/setup/wifi")
        async def configure_wifi(credentials: WiFiCredentials) -> JSONResponse:
            """Configure WiFi credentials."""
            logger.info(f"Configuring WiFi for SSID: {credentials.ssid}")

            try:
                # Store credentials
                self._wifi_credentials = credentials

                # Save to file
                await self._save_wifi_credentials(credentials)

                # Notify callback
                if self.on_wifi_configured:
                    await self._maybe_await(
                        self.on_wifi_configured(credentials.ssid)
                    )

                return JSONResponse(
                    content={
                        "success": True,
                        "message": "WiFi configured. Connecting...",
                        "redirect_url": self.dashboard_url,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to configure WiFi: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to configure WiFi: {str(e)}",
                )

        @app.post("/api/setup/wifi/test")
        async def test_wifi_connection() -> JSONResponse:
            """Test WiFi connection with current credentials."""
            if not self._wifi_credentials:
                raise HTTPException(
                    status_code=400,
                    detail="No WiFi credentials configured",
                )

            success = await self._test_wifi_connection(self._wifi_credentials)

            if success:
                return JSONResponse(
                    content={
                        "success": True,
                        "message": "Connected successfully!",
                        "redirect_url": self.dashboard_url,
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "success": False,
                        "message": "Could not connect. Please check password.",
                    },
                    status_code=400,
                )

        @app.get("/api/setup/progress")
        async def get_progress() -> SetupProgress:
            """Get current setup progress."""
            return SetupProgress(
                step=1 if not self._wifi_credentials else 2,
                total_steps=6,
                current_step_name="Configure WiFi" if not self._wifi_credentials else "Connecting...",
                wifi_configured=self._wifi_credentials is not None,
                name_configured=False,
            )

        # Mount static files if directory exists
        if STATIC_DIR.exists():
            app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        return app

    async def start(self) -> None:
        """Start the captive portal server."""
        logger.info(f"Starting captive portal on {self.host}:{self.port}")

        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        # Run in background
        asyncio.create_task(self._server.serve())
        logger.info(f"Captive portal running at http://{self.gateway_ip}/setup")

    async def stop(self) -> None:
        """Stop the captive portal server."""
        if self._server:
            self._server.should_exit = True
            logger.info("Captive portal stopped")

    def _get_setup_html(self) -> str:
        """Generate the setup wizard HTML page."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nightwatch Setup</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e8e8e8;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            font-size: 28px;
            font-weight: 600;
            color: #7c3aed;
        }
        .logo p {
            color: #888;
            margin-top: 8px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .card h2 {
            font-size: 18px;
            margin-bottom: 16px;
            color: #fff;
        }
        .network-list {
            list-style: none;
            max-height: 200px;
            overflow-y: auto;
        }
        .network-item {
            padding: 12px 16px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        .network-item:hover {
            background: rgba(124, 58, 237, 0.2);
        }
        .network-item.selected {
            background: rgba(124, 58, 237, 0.3);
            border: 1px solid #7c3aed;
        }
        .signal-strength {
            color: #888;
            font-size: 12px;
        }
        input[type="password"], input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.2);
            color: #fff;
            font-size: 16px;
            margin-top: 12px;
        }
        input:focus {
            outline: none;
            border-color: #7c3aed;
        }
        button {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 8px;
            background: #7c3aed;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
            transition: background 0.2s;
        }
        button:hover {
            background: #6d28d9;
        }
        button:disabled {
            background: #444;
            cursor: not-allowed;
        }
        .status {
            text-align: center;
            padding: 20px;
            color: #888;
        }
        .status.error {
            color: #ef4444;
        }
        .status.success {
            color: #22c55e;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #888;
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Nightwatch</h1>
            <p>Let's get you set up</p>
        </div>

        <div class="card" id="wifi-card">
            <h2>1. Connect to WiFi</h2>
            <div id="scanning" class="status">
                <span class="spinner"></span> Scanning for networks...
            </div>
            <ul class="network-list hidden" id="network-list"></ul>
            <input type="password" id="password" placeholder="Enter WiFi password" class="hidden">
            <button id="connect-btn" class="hidden" disabled>Connect</button>
            <div id="connect-status" class="status hidden"></div>
        </div>

        <div class="card hidden" id="success-card">
            <h2>Connected!</h2>
            <p class="status success">Redirecting to dashboard...</p>
        </div>
    </div>

    <script>
        let selectedNetwork = null;
        const networkList = document.getElementById('network-list');
        const passwordInput = document.getElementById('password');
        const connectBtn = document.getElementById('connect-btn');
        const connectStatus = document.getElementById('connect-status');
        const scanningDiv = document.getElementById('scanning');

        // Scan for networks on load
        scanNetworks();

        async function scanNetworks() {
            try {
                const res = await fetch('/api/setup/wifi/scan');
                const data = await res.json();

                scanningDiv.classList.add('hidden');
                networkList.classList.remove('hidden');

                if (data.networks.length === 0) {
                    networkList.innerHTML = '<li class="status">No networks found. <button onclick="scanNetworks()">Retry</button></li>';
                    return;
                }

                networkList.innerHTML = data.networks.map(n => `
                    <li class="network-item" data-ssid="${n.ssid}" onclick="selectNetwork(this, '${n.ssid}')">
                        <span>${n.ssid}</span>
                        <span class="signal-strength">${n.signal}%</span>
                    </li>
                `).join('');
            } catch (e) {
                scanningDiv.innerHTML = '<span class="error">Failed to scan. <button onclick="scanNetworks()">Retry</button></span>';
            }
        }

        function selectNetwork(el, ssid) {
            document.querySelectorAll('.network-item').forEach(item => item.classList.remove('selected'));
            el.classList.add('selected');
            selectedNetwork = ssid;
            passwordInput.classList.remove('hidden');
            connectBtn.classList.remove('hidden');
            passwordInput.focus();
            updateConnectButton();
        }

        passwordInput.addEventListener('input', updateConnectButton);

        function updateConnectButton() {
            connectBtn.disabled = !selectedNetwork || passwordInput.value.length < 8;
        }

        connectBtn.addEventListener('click', async () => {
            if (!selectedNetwork) return;

            connectBtn.disabled = true;
            connectBtn.textContent = 'Connecting...';
            connectStatus.classList.remove('hidden', 'error');
            connectStatus.innerHTML = '<span class="spinner"></span> Connecting to ' + selectedNetwork + '...';

            try {
                const res = await fetch('/api/setup/wifi', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ssid: selectedNetwork,
                        password: passwordInput.value
                    })
                });

                const data = await res.json();

                if (data.success) {
                    document.getElementById('wifi-card').classList.add('hidden');
                    document.getElementById('success-card').classList.remove('hidden');
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 2000);
                } else {
                    throw new Error(data.message || 'Connection failed');
                }
            } catch (e) {
                connectStatus.classList.add('error');
                connectStatus.textContent = e.message || 'Failed to connect. Check password and try again.';
                connectBtn.disabled = false;
                connectBtn.textContent = 'Connect';
            }
        });
    </script>
</body>
</html>"""

    def _get_ios_captive_html(self) -> str:
        """Generate iOS captive portal detection response."""
        # iOS looks for specific content - NOT returning "Success" triggers portal
        return """<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=http://""" + self.gateway_ip + """/setup">
</head>
<body>
    <script>window.location='http://""" + self.gateway_ip + """/setup';</script>
</body>
</html>"""

    async def _scan_wifi(self) -> list[dict]:
        """Scan for available WiFi networks."""
        try:
            result = await asyncio.create_subprocess_exec(
                "iwlist", "wlan0", "scan",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            networks = []
            current = {}

            for line in stdout.decode().split("\n"):
                line = line.strip()
                if "ESSID:" in line:
                    ssid = line.split('"')[1] if '"' in line else ""
                    if ssid and ssid not in [n["ssid"] for n in networks]:
                        current["ssid"] = ssid
                elif "Signal level=" in line:
                    # Convert dBm to percentage
                    try:
                        dbm = int(line.split("Signal level=")[1].split(" ")[0])
                        signal = max(0, min(100, 2 * (dbm + 100)))
                        current["signal"] = signal
                    except (ValueError, IndexError):
                        current["signal"] = 50

                if "ssid" in current and "signal" in current:
                    networks.append(current)
                    current = {}

            # Sort by signal strength
            networks.sort(key=lambda x: x.get("signal", 0), reverse=True)
            return networks[:10]  # Top 10 networks

        except Exception as e:
            logger.error(f"WiFi scan failed: {e}")
            # Return mock data for development
            return [
                {"ssid": "MyHomeNetwork", "signal": 85},
                {"ssid": "Neighbor_WiFi", "signal": 45},
            ]

    async def _save_wifi_credentials(self, credentials: WiFiCredentials) -> None:
        """Save WiFi credentials to wpa_supplicant format."""
        from nightwatch.setup.provisioning import WiFiProvisioner

        provisioner = WiFiProvisioner()
        await provisioner.save_credentials(credentials.ssid, credentials.password)

    async def _test_wifi_connection(self, credentials: WiFiCredentials) -> bool:
        """Test connection to WiFi network."""
        from nightwatch.setup.provisioning import WiFiProvisioner

        provisioner = WiFiProvisioner()
        return await provisioner.test_connection()

    async def _maybe_await(self, coro_or_result: Any) -> Any:
        """Await if coroutine, otherwise return directly."""
        if asyncio.iscoroutine(coro_or_result):
            return await coro_or_result
        return coro_or_result


# =============================================================================
# Development / Testing Entry Point
# =============================================================================


def main():
    """Run the captive portal in development mode.

    Usage:
        python -m nightwatch.setup.portal [--port PORT] [--dev]

    In dev mode:
        - Runs on localhost:8080 (not port 80 which requires root)
        - WiFi scan returns mock data
        - WiFi save skips wpa_supplicant (saves to temp file)
        - No hotspot required
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="nightwatch.setup.portal",
        description="Captive portal server for Nightwatch setup",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run on (default: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode - use mock data, skip hardware",
    )

    args = parser.parse_args()

    # In dev mode, override save to use temp directory
    dev_mode = args.dev

    if dev_mode:
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="nightwatch-"))
        print(f"📁 Dev mode: config will be saved to {temp_dir}")

    async def on_wifi_configured(ssid: str):
        print(f"✅ WiFi configured: {ssid}")
        if dev_mode:
            print(f"   (dev mode - not actually connecting)")

    portal = CaptivePortal(
        host=args.host,
        port=args.port,
        gateway_ip="127.0.0.1",  # localhost for dev
        on_wifi_configured=on_wifi_configured,
    )

    # In dev mode, patch the save function to use temp directory
    if dev_mode:
        original_save = portal._save_wifi_credentials

        async def mock_save(credentials: WiFiCredentials) -> None:
            config_file = temp_dir / "wifi.conf"
            config_file.write_text(f"ssid={credentials.ssid}\npassword={credentials.password}\n")
            print(f"📝 Saved credentials to {config_file}")

        portal._save_wifi_credentials = mock_save

    print("=" * 50)
    print("🌙 Nightwatch Captive Portal")
    print("=" * 50)
    print(f"  Mode: {'Development' if dev_mode else 'Production'}")
    print(f"  URL:  http://{args.host}:{args.port}/setup")
    print()
    print("Press Ctrl+C to stop")
    print()

    async def run():
        await portal.start()

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await portal.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n👋 Stopped")


if __name__ == "__main__":
    main()
