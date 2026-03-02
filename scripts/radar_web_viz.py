#!/usr/bin/env python3
"""
Real-time radar signal visualizer - web version.

Serves a webpage that shows the raw radar Y signal as a live waveform.
Access at http://nightwatch.local:8888

Usage:
    python3 radar_web_viz.py [--port 8888] [--device /dev/ttyUSB0]
"""

import argparse
import asyncio
import json
import struct
import threading
import time
from collections import deque
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

# Try to import websockets, fall back to polling if not available
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

import serial

HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])

# Global data buffer
data_buffer = deque(maxlen=500)  # ~50 seconds at 10Hz
data_lock = threading.Lock()

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Radar Signal Visualizer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #1a1a2e;
            color: #eee;
            margin: 0;
            padding: 20px;
        }
        h1 { margin: 0 0 10px 0; font-size: 1.5em; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .tab {
            padding: 8px 16px;
            background: #16213e;
            border: none;
            border-radius: 6px;
            color: #888;
            cursor: pointer;
            font-size: 0.9em;
        }
        .tab.active {
            background: #3b82f6;
            color: white;
        }
        .view { display: none; }
        .view.active { display: block; }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            font-size: 0.9em;
            flex-wrap: wrap;
        }
        .stat {
            background: #16213e;
            padding: 10px 15px;
            border-radius: 8px;
        }
        .stat-label { color: #888; font-size: 0.8em; }
        .stat-value { font-size: 1.4em; font-weight: bold; }
        .stat-value.good { color: #4ade80; }
        .stat-value.warn { color: #fbbf24; }
        .charts {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        .chart-container {
            background: #16213e;
            border-radius: 8px;
            padding: 15px;
            height: 250px;
        }
        .chart-container h3 {
            margin: 0 0 10px 0;
            font-size: 0.95em;
            color: #aaa;
        }
        .chart-wrapper {
            height: 200px;
        }
        .note {
            margin-top: 15px;
            color: #666;
            font-size: 0.85em;
        }
        /* Radar view (top-down) */
        .radar-container {
            background: #16213e;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        #radar-canvas {
            background: #0d1421;
            border-radius: 8px;
        }
        .radar-legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.85em;
            color: #888;
        }
        .radar-legend span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        .dot.target { background: #3b82f6; }
        .dot.zone { background: rgba(16, 185, 129, 0.3); border: 1px solid #10b981; }
    </style>
</head>
<body>
    <h1>Radar Signal Visualizer</h1>

    <div class="tabs">
        <button class="tab active" onclick="showView('signal')">Signal View</button>
        <button class="tab" onclick="showView('radar')">Radar View (Aiming)</button>
    </div>

    <!-- Signal View -->
    <div id="signal-view" class="view active">
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Distance</div>
                <div class="stat-value" id="distance">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Raw Std Dev</div>
                <div class="stat-value" id="std-raw">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Smoothed Std Dev</div>
                <div class="stat-value" id="std-smooth">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Samples/sec</div>
                <div class="stat-value" id="rate">--</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <h3>Raw Signal</h3>
                <div class="chart-wrapper">
                    <canvas id="chart-raw"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <h3>Smoothed (10-sample moving avg)</h3>
                <div class="chart-wrapper">
                    <canvas id="chart-smooth"></canvas>
                </div>
            </div>
        </div>

        <p class="note">
            Breathing shows as a smooth wave (5-15mm amplitude, 0.2-0.3 Hz).<br>
            The smoothed chart filters out noise - look for rhythmic breathing pattern there.
        </p>
    </div>

    <!-- Radar View (Top-down aiming) -->
    <div id="radar-view" class="view">
        <div class="radar-container">
            <h3>Top-Down View (Radar at top, looking down)</h3>
            <canvas id="radar-canvas" width="500" height="400"></canvas>
            <div class="radar-legend">
                <span><div class="dot target"></div> Target</span>
                <span><div class="dot" style="background: rgba(251, 191, 36, 0.4);"></div> Caution (0.5-1m, 3-4m)</span>
                <span><div class="dot zone"></div> Ideal (1-3m)</span>
            </div>
            <p class="note" style="margin-top: 15px;">
                Aim the radar so the target appears in the green zone (1-3m).<br>
                Yellow zones are usable but not optimal for breathing detection.
            </p>
        </div>
        <div class="stats" style="margin-top: 15px;">
            <div class="stat">
                <div class="stat-label">Target X</div>
                <div class="stat-value" id="target-x">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Target Y</div>
                <div class="stat-value" id="target-y">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Distance</div>
                <div class="stat-value" id="target-dist">--</div>
            </div>
            <div class="stat">
                <div class="stat-label">Angle</div>
                <div class="stat-value" id="target-angle">--</div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        function showView(view) {
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(view + '-view').classList.add('active');
            event.target.classList.add('active');
        }

        // Radar canvas drawing
        const radarCanvas = document.getElementById('radar-canvas');
        const radarCtx = radarCanvas.getContext('2d');
        let lastTarget = { x: 0, y: 0 };

        function drawRadarView(x, y, distance) {
            const W = radarCanvas.width;
            const H = radarCanvas.height;
            const scale = H / 4000;  // 4 meters max range

            radarCtx.clearRect(0, 0, W, H);

            // Draw distance rings
            radarCtx.strokeStyle = '#333';
            radarCtx.lineWidth = 1;
            for (let d = 1000; d <= 4000; d += 1000) {
                radarCtx.beginPath();
                radarCtx.arc(W/2, 0, d * scale, 0, Math.PI);
                radarCtx.stroke();
                radarCtx.fillStyle = '#555';
                radarCtx.font = '11px sans-serif';
                radarCtx.fillText((d/1000) + 'm', W/2 + d*scale - 15, 15);
            }

            // Draw zones: 0.5-1m yellow, 1-3m green, 3-4m yellow
            // Yellow zone (0.5-1m) - too close
            radarCtx.fillStyle = 'rgba(251, 191, 36, 0.15)';
            radarCtx.beginPath();
            radarCtx.moveTo(W/2, 0);
            radarCtx.arc(W/2, 0, 1000 * scale, 0, Math.PI);
            radarCtx.arc(W/2, 0, 500 * scale, Math.PI, 0, true);
            radarCtx.closePath();
            radarCtx.fill();
            radarCtx.strokeStyle = '#fbbf24';
            radarCtx.lineWidth = 1;
            radarCtx.stroke();

            // Green zone (1-3m) - ideal
            radarCtx.fillStyle = 'rgba(16, 185, 129, 0.15)';
            radarCtx.beginPath();
            radarCtx.moveTo(W/2, 0);
            radarCtx.arc(W/2, 0, 3000 * scale, 0, Math.PI);
            radarCtx.arc(W/2, 0, 1000 * scale, Math.PI, 0, true);
            radarCtx.closePath();
            radarCtx.fill();
            radarCtx.strokeStyle = '#10b981';
            radarCtx.lineWidth = 2;
            radarCtx.stroke();

            // Yellow zone (3-4m) - getting far
            radarCtx.fillStyle = 'rgba(251, 191, 36, 0.15)';
            radarCtx.beginPath();
            radarCtx.moveTo(W/2, 0);
            radarCtx.arc(W/2, 0, 4000 * scale, 0, Math.PI);
            radarCtx.arc(W/2, 0, 3000 * scale, Math.PI, 0, true);
            radarCtx.closePath();
            radarCtx.fill();
            radarCtx.strokeStyle = '#fbbf24';
            radarCtx.lineWidth = 1;
            radarCtx.stroke();

            // Draw center line
            radarCtx.strokeStyle = '#444';
            radarCtx.setLineDash([5, 5]);
            radarCtx.beginPath();
            radarCtx.moveTo(W/2, 0);
            radarCtx.lineTo(W/2, H);
            radarCtx.stroke();
            radarCtx.setLineDash([]);

            // Draw radar position (top center)
            radarCtx.fillStyle = '#f59e0b';
            radarCtx.beginPath();
            radarCtx.arc(W/2, 5, 8, 0, Math.PI * 2);
            radarCtx.fill();
            radarCtx.fillStyle = '#888';
            radarCtx.fillText('RADAR', W/2 - 20, 28);

            // Draw target (if valid)
            if (Math.abs(y) > 100) {  // Valid target
                const targetX = W/2 + (x * scale);
                const targetY = Math.abs(y) * scale;

                // Smooth the position
                lastTarget.x = lastTarget.x * 0.7 + targetX * 0.3;
                lastTarget.y = lastTarget.y * 0.7 + targetY * 0.3;

                // Draw target
                radarCtx.fillStyle = '#3b82f6';
                radarCtx.beginPath();
                radarCtx.arc(lastTarget.x, lastTarget.y, 12, 0, Math.PI * 2);
                radarCtx.fill();

                // Target label
                radarCtx.fillStyle = '#fff';
                radarCtx.font = 'bold 11px sans-serif';
                radarCtx.fillText(distance.toFixed(2) + 'm', lastTarget.x + 15, lastTarget.y + 4);
            }
        }

        // Moving average function
        function movingAverage(data, windowSize) {
            const result = [];
            for (let i = 0; i < data.length; i++) {
                const start = Math.max(0, i - windowSize + 1);
                const window = data.slice(start, i + 1);
                const avg = window.reduce((a, b) => a + b, 0) / window.length;
                result.push(avg);
            }
            return result;
        }

        // Calculate std dev
        function stdDev(arr) {
            if (arr.length === 0) return 0;
            const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
            const squaredDiffs = arr.map(x => Math.pow(x - mean, 2));
            return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / arr.length);
        }

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    display: true,
                    grid: { color: '#333' },
                    ticks: { color: '#666', maxTicksLimit: 5 }
                },
                y: {
                    grid: { color: '#333' },
                    ticks: { color: '#666' }
                }
            }
        };

        // Raw chart
        const ctxRaw = document.getElementById('chart-raw').getContext('2d');
        const chartRaw = new Chart(ctxRaw, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Raw Y (mm)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.2,
                    pointRadius: 0,
                    borderWidth: 1.5,
                }]
            },
            options: chartOptions
        });

        // Smoothed chart
        const ctxSmooth = document.getElementById('chart-smooth').getContext('2d');
        const chartSmooth = new Chart(ctxSmooth, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Smoothed Y (mm)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2,
                }]
            },
            options: chartOptions
        });

        // Fetch data via polling
        async function fetchData() {
            try {
                const resp = await fetch('/data');
                const data = await resp.json();

                if (data.y_values.length === 0) return;

                // Calculate baseline
                const baseline = data.y_values.reduce((a,b) => a+b, 0) / data.y_values.length;

                // Raw data (deviation from mean)
                const rawData = data.y_values.map(y => y - baseline);
                const labels = rawData.map((_, i) => i);

                // Smoothed data (10-sample moving average)
                const smoothedData = movingAverage(rawData, 10);

                // Update raw chart
                chartRaw.data.labels = labels;
                chartRaw.data.datasets[0].data = rawData;
                chartRaw.update('none');

                // Update smoothed chart
                chartSmooth.data.labels = labels;
                chartSmooth.data.datasets[0].data = smoothedData;
                chartSmooth.update('none');

                // Update stats
                document.getElementById('distance').textContent =
                    data.distance ? data.distance.toFixed(2) + 'm' : '--';

                const rawStd = stdDev(rawData);
                const rawStdEl = document.getElementById('std-raw');
                rawStdEl.textContent = rawStd.toFixed(1) + 'mm';
                rawStdEl.className = 'stat-value ' + (rawStd > 5 && rawStd < 30 ? 'good' : 'warn');

                const smoothStd = stdDev(smoothedData);
                const smoothStdEl = document.getElementById('std-smooth');
                smoothStdEl.textContent = smoothStd.toFixed(1) + 'mm';
                smoothStdEl.className = 'stat-value ' + (smoothStd > 5 && smoothStd < 20 ? 'good' : 'warn');

                document.getElementById('rate').textContent =
                    data.sample_rate ? data.sample_rate.toFixed(1) : '--';

                // Update radar view
                if (data.x !== undefined && data.y !== undefined) {
                    drawRadarView(data.x, data.y, data.distance || 0);

                    // Update radar stats
                    document.getElementById('target-x').textContent = data.x + 'mm';
                    document.getElementById('target-y').textContent = data.y + 'mm';
                    document.getElementById('target-dist').textContent =
                        data.distance ? data.distance.toFixed(2) + 'm' : '--';
                    const angle = Math.atan2(data.x, Math.abs(data.y)) * 180 / Math.PI;
                    document.getElementById('target-angle').textContent = angle.toFixed(0) + '°';
                }

            } catch (e) {
                console.error('Fetch error:', e);
            }
        }

        // Poll every 200ms
        setInterval(fetchData, 200);
        fetchData();
    </script>
</body>
</html>
"""


class RadarHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with data_lock:
                y_values = [d['y'] for d in data_buffer]

                if y_values:
                    import numpy as np
                    y_std = float(np.std(y_values))
                    distance = data_buffer[-1].get('distance', 0) if data_buffer else 0
                else:
                    y_std = 0
                    distance = 0

                # Calculate sample rate
                if len(data_buffer) >= 2:
                    time_span = data_buffer[-1]['t'] - data_buffer[0]['t']
                    sample_rate = len(data_buffer) / time_span if time_span > 0 else 0
                else:
                    sample_rate = 0

                # Get latest X/Y for radar view
                latest_x = data_buffer[-1].get('x', 0) if data_buffer else 0
                latest_y = data_buffer[-1].get('y', 0) if data_buffer else 0

                response = {
                    'y_values': y_values[-200:],  # Last 200 samples
                    'y_std': y_std,
                    'distance': distance,
                    'sample_rate': sample_rate,
                    'x': latest_x,
                    'y': latest_y,
                }

            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress logging


def radar_reader_thread(device: str):
    """Background thread that reads from radar."""
    try:
        import numpy as np
    except ImportError:
        print("WARNING: numpy not available for stats")
        np = None

    ser = serial.Serial(device, 256000, timeout=0.1)
    print(f"Radar connected on {device}")

    buffer = bytearray()

    while True:
        try:
            # Read all available data
            data = ser.read(256)
            if data:
                buffer.extend(data)

            # Process all complete frames in buffer
            while len(buffer) >= 30:
                idx = buffer.find(HEADER)
                if idx == -1:
                    buffer = buffer[-3:]  # Keep potential partial header
                    break
                if idx > 0:
                    buffer = buffer[idx:]  # Discard before header
                if len(buffer) < 30:
                    break

                # Parse frame
                x, y, spd, _ = struct.unpack('<hhhH', bytes(buffer[4:12]))
                if y & 0x8000:
                    y = -(y & 0x7FFF)
                if x & 0x8000:
                    x = -(x & 0x7FFF)

                if y != 0:  # Valid reading
                    distance = ((x**2 + y**2)**0.5) / 1000

                    with data_lock:
                        data_buffer.append({
                            't': time.time(),
                            'y': y,
                            'x': x,
                            'distance': distance,
                        })

                buffer = buffer[30:]  # Move to next frame

            time.sleep(0.01)  # Small sleep to prevent CPU spin

        except Exception as e:
            print(f"Radar read error: {e}")
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Radar Signal Web Visualizer")
    parser.add_argument("--port", type=int, default=8888, help="Web server port")
    parser.add_argument("--device", default="/dev/ttyUSB0", help="Serial device")
    args = parser.parse_args()

    # Start radar reader thread
    radar_thread = threading.Thread(target=radar_reader_thread, args=(args.device,), daemon=True)
    radar_thread.start()

    # Start web server
    with socketserver.TCPServer(("", args.port), RadarHandler) as httpd:
        print(f"\nRadar visualizer running at http://nightwatch.local:{args.port}")
        print("Press Ctrl+C to stop\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped")


if __name__ == "__main__":
    main()
