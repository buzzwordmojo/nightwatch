#!/usr/bin/env python3
"""
Real-time radar signal visualizer.

Shows Y-position deviation as a live waveform in the terminal.
Breathing appears as a rhythmic wave pattern.
"""

import serial
import struct
import sys
import time

HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

    print(f"Connecting to {port}...")
    ser = serial.Serial(port, 256000, timeout=0.5)

    WIDTH = 50
    baseline = None
    y_history = []

    print("\nLive Y-position (breathing shows as wave)")
    print("=" * (WIDTH + 30))
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            data = ser.read(64)
            idx = data.find(HEADER)

            if idx >= 0 and idx + 12 <= len(data):
                x, y, spd, _ = struct.unpack('<hhhH', data[idx+4:idx+12])
                if y & 0x8000:
                    y = -(y & 0x7FFF)

                if y != 0:
                    if baseline is None:
                        baseline = y

                    # Track history for stats
                    y_history.append(y)
                    if len(y_history) > 100:
                        y_history.pop(0)

                    # Calculate stats
                    y_mean = sum(y_history) / len(y_history)
                    y_std = (sum((v - y_mean)**2 for v in y_history) / len(y_history)) ** 0.5

                    # Deviation from rolling mean (shows breathing better)
                    dev = y - y_mean

                    # Scale: 10mm = half width
                    scaled = int(dev / 2)
                    scaled = max(-WIDTH//2, min(WIDTH//2, scaled))

                    # Build visualization bar
                    bar = [' '] * WIDTH
                    center = WIDTH // 2
                    bar[center] = '|'

                    pos = center + scaled
                    if 0 <= pos < WIDTH:
                        bar[pos] = '*'

                    # Draw range indicator
                    bar_str = ''.join(bar)
                    dist = ((x**2 + y**2)**0.5) / 1000

                    # Color based on deviation
                    if abs(dev) > 10:
                        marker = ">>>" if dev > 0 else "<<<"
                    else:
                        marker = "   "

                    print(f"[{bar_str}] {marker} std={y_std:5.1f}mm dist={dist:.2f}m", end='\r')

            time.sleep(0.08)

    except KeyboardInterrupt:
        print("\n\nStopped.")
        if y_history:
            y_mean = sum(y_history) / len(y_history)
            y_std = (sum((v - y_mean)**2 for v in y_history) / len(y_history)) ** 0.5
            print(f"Final stats: mean={y_mean:.0f}mm, std={y_std:.1f}mm")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
