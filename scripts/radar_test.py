#!/usr/bin/env python3
"""
Radar sensor test utility for LD2450.

Tests hardware wiring, target tracking, and vital sign extraction.

Usage:
    python3 radar_test.py                    # Basic connectivity test
    python3 radar_test.py --mode target      # Target tracking test
    python3 radar_test.py --mode breathing   # Breathing detection test
    python3 radar_test.py --mode movement    # Movement detection test
    python3 radar_test.py --mode presence    # Presence detection test
    python3 radar_test.py --mode all         # Run all tests
"""

import argparse
import struct
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip3 install pyserial")
    sys.exit(1)

try:
    import numpy as np
    from scipy import signal as scipy_signal
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy/numpy not installed. Vital sign extraction disabled.")
    print("         Run: pip3 install numpy scipy")


# ============================================================================
# LD2450 Protocol
# ============================================================================

FRAME_HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])
FRAME_FOOTER = bytes([0x55, 0xCC])


@dataclass
class Target:
    """Radar target data."""
    x: int      # mm (horizontal, -ve=left, +ve=right)
    y: int      # mm (depth/distance)
    speed: int  # cm/s (signed)

    @property
    def distance_m(self) -> float:
        return ((self.x**2 + self.y**2) ** 0.5) / 1000.0

    @property
    def angle_deg(self) -> float:
        import math
        if self.y == 0:
            return 90.0 if self.x > 0 else -90.0
        return math.degrees(math.atan2(self.x, self.y))

    @property
    def is_valid(self) -> bool:
        return not (self.x == 0 and self.y == 0 and self.speed == 0)


def parse_frame(data: bytes) -> list[Target]:
    """Parse LD2450 frame, return list of valid targets."""
    if len(data) < 30:
        return []

    idx = data.find(FRAME_HEADER)
    if idx == -1 or idx + 30 > len(data):
        return []

    frame = data[idx:idx+30]
    if frame[28:30] != FRAME_FOOTER:
        return []

    targets = []
    for i in range(3):
        offset = 4 + (i * 8)
        x, y, speed, _ = struct.unpack("<hhhH", frame[offset:offset+8])

        # Handle sign bits
        if x & 0x8000:
            x = -(x & 0x7FFF)
        if y & 0x8000:
            y = -(y & 0x7FFF)

        t = Target(x=x, y=y, speed=speed)
        if t.is_valid:
            targets.append(t)

    return targets


def read_targets(ser: serial.Serial, timeout: float = 0.5) -> list[Target]:
    """Read one frame and return targets."""
    ser.reset_input_buffer()
    time.sleep(0.05)
    data = ser.read(100)
    return parse_frame(data)


# ============================================================================
# Signal Processing (simplified versions)
# ============================================================================

class SimpleBreathingDetector:
    """Simplified breathing rate detector."""

    def __init__(self, sample_rate: float = 10.0):
        self.sample_rate = sample_rate
        self.y_buffer = deque(maxlen=int(sample_rate * 15))  # 15 sec window
        self.last_rate: Optional[float] = None
        self.last_confidence: float = 0.0

    def update(self, y_mm: float) -> tuple[Optional[float], float]:
        """Update with Y position, return (rate_bpm, confidence)."""
        self.y_buffer.append(y_mm)

        if len(self.y_buffer) < 50:  # Need 5 seconds minimum
            return None, 0.0

        if not HAS_SCIPY:
            return None, 0.0

        # Convert to array and remove mean
        y = np.array(self.y_buffer)
        y = y - np.mean(y)

        # Bandpass filter 0.1-0.5 Hz (6-30 BPM)
        try:
            nyq = self.sample_rate / 2
            b, a = scipy_signal.butter(3, [0.1/nyq, 0.5/nyq], btype='band')
            filtered = scipy_signal.filtfilt(b, a, y)
        except Exception:
            return self.last_rate, 0.3

        # Autocorrelation to find period
        n = len(filtered)
        autocorr = np.correlate(filtered, filtered, mode='full')[n-1:]
        autocorr = autocorr / (autocorr[0] + 1e-10)

        # Find first peak (breathing period)
        min_lag = int(self.sample_rate * 2)   # 30 BPM max
        max_lag = int(self.sample_rate * 10)  # 6 BPM min
        max_lag = min(max_lag, len(autocorr) - 1)

        if min_lag >= max_lag:
            return self.last_rate, 0.3

        search = autocorr[min_lag:max_lag]
        try:
            peaks, _ = scipy_signal.find_peaks(search, height=0.2, distance=int(self.sample_rate))
        except Exception:
            return self.last_rate, 0.3

        if len(peaks) == 0:
            return self.last_rate, 0.3

        peak_lag = peaks[0] + min_lag
        period_sec = peak_lag / self.sample_rate
        rate_bpm = 60.0 / period_sec
        confidence = float(search[peaks[0]])

        if 5 < rate_bpm < 35:
            self.last_rate = rate_bpm
            self.last_confidence = confidence

        return self.last_rate, self.last_confidence


class SimpleMovementDetector:
    """Simplified movement detector."""

    def __init__(self, sample_rate: float = 10.0):
        self.x_buffer = deque(maxlen=int(sample_rate * 2))
        self.y_buffer = deque(maxlen=int(sample_rate * 2))

    def update(self, x: float, y: float) -> tuple[float, bool]:
        """Update and return (level 0-1, is_macro)."""
        self.x_buffer.append(x)
        self.y_buffer.append(y)

        if len(self.x_buffer) < 5:
            return 0.0, False

        x_var = np.var(list(self.x_buffer)) if HAS_SCIPY else 0
        y_var = np.var(list(self.y_buffer)) if HAS_SCIPY else 0
        total_var = (x_var + y_var) ** 0.5

        level = min(1.0, total_var / 100.0)  # 100mm = full scale
        is_macro = total_var > 100

        return level, is_macro


# ============================================================================
# Test Modes
# ============================================================================

def test_connectivity(ser: serial.Serial) -> bool:
    """Test basic connectivity - verify we get valid frames."""
    print("\n=== CONNECTIVITY TEST ===\n")

    ser.reset_input_buffer()
    time.sleep(0.3)
    data = ser.read(200)

    print(f"Bytes received: {len(data)}")

    if len(data) == 0:
        print("FAIL: No data received")
        print("      Check: Power (5V), TX→RXD, RX←TXD wiring")
        return False

    has_header = FRAME_HEADER in data
    print(f"Frame header found: {has_header}")

    if has_header:
        print(f"Hex sample: {data[:40].hex()}")
        print("\nPASS: Radar communication OK")
        return True
    else:
        print(f"Hex (raw): {data[:60].hex()}")
        print("\nFAIL: No valid frame headers")
        print("      Data is garbled - check TX/RX wiring")
        return False


def test_target_tracking(ser: serial.Serial, duration: float = 5.0):
    """Test target tracking - verify position updates."""
    print(f"\n=== TARGET TRACKING TEST ({duration}s) ===")
    print("Move around in front of the radar...\n")

    start = time.time()
    readings = 0
    last_print = 0

    while time.time() - start < duration:
        targets = read_targets(ser)

        if targets:
            t = targets[0]  # Primary target
            readings += 1

            now = time.time()
            if now - last_print > 0.3:  # Print every 300ms
                print(f"  Distance: {t.distance_m:.2f}m  "
                      f"Angle: {t.angle_deg:+.0f}°  "
                      f"Speed: {t.speed:+d} cm/s  "
                      f"(x={t.x}, y={t.y})")
                last_print = now

        time.sleep(0.1)

    print(f"\nReadings: {readings}")
    if readings > 10:
        print("PASS: Target tracking working")
    else:
        print("WARN: Few readings - ensure you're in radar FOV (0.3-6m)")


def test_breathing(ser: serial.Serial, duration: float = 30.0):
    """Test breathing detection - sit still for analysis."""
    print(f"\n=== BREATHING DETECTION TEST ({duration}s) ===")
    print("Sit or lie still 1-2m from radar...\n")

    if not HAS_SCIPY:
        print("ERROR: scipy required for breathing detection")
        return

    detector = SimpleBreathingDetector(sample_rate=10.0)
    start = time.time()
    last_print = 0

    while time.time() - start < duration:
        targets = read_targets(ser)

        if targets:
            t = targets[0]
            rate, conf = detector.update(t.y)

            now = time.time()
            if now - last_print > 1.0:  # Print every second
                elapsed = now - start
                if rate:
                    print(f"  [{elapsed:5.1f}s] Breathing: {rate:.1f} BPM  "
                          f"(confidence: {conf:.2f})  "
                          f"distance: {t.distance_m:.2f}m")
                else:
                    print(f"  [{elapsed:5.1f}s] Collecting data... "
                          f"distance: {t.distance_m:.2f}m")
                last_print = now

        time.sleep(0.1)

    final_rate, final_conf = detector.last_rate, detector.last_confidence
    print(f"\nFinal: {final_rate:.1f} BPM (confidence: {final_conf:.2f})" if final_rate else "\nNo breathing detected")

    if final_rate and 8 < final_rate < 25 and final_conf > 0.4:
        print("PASS: Breathing detection working")
    elif final_rate:
        print("WARN: Readings present but low confidence - try sitting more still")
    else:
        print("FAIL: No breathing detected - check positioning")


def test_movement(ser: serial.Serial, duration: float = 20.0):
    """Test movement detection - alternate still/moving."""
    print(f"\n=== MOVEMENT DETECTION TEST ({duration}s) ===")
    print("First 10s: Sit still")
    print("Last 10s: Move around\n")

    if not HAS_SCIPY:
        print("ERROR: scipy required for movement detection")
        return

    detector = SimpleMovementDetector()
    start = time.time()
    last_print = 0
    macro_count = 0
    still_count = 0

    while time.time() - start < duration:
        targets = read_targets(ser)

        if targets:
            t = targets[0]
            level, is_macro = detector.update(t.x, t.y)

            if is_macro:
                macro_count += 1
            else:
                still_count += 1

            now = time.time()
            elapsed = now - start
            phase = "MOVE NOW!" if elapsed > 10 else "Stay still"

            if now - last_print > 0.5:
                status = "MACRO MOVEMENT" if is_macro else "still/micro"
                bar = "#" * int(level * 20)
                print(f"  [{elapsed:5.1f}s] [{phase:10s}] {status:15s} [{bar:20s}] {level:.2f}")
                last_print = now

        time.sleep(0.1)

    print(f"\nMacro movements: {macro_count}, Still periods: {still_count}")
    if macro_count > 10 and still_count > 30:
        print("PASS: Movement detection working")
    else:
        print("WARN: Check results - expected both macro and still readings")


def test_presence(ser: serial.Serial, duration: float = 15.0):
    """Test presence detection - walk in/out of view."""
    print(f"\n=== PRESENCE DETECTION TEST ({duration}s) ===")
    print("Walk in and out of radar view...\n")

    start = time.time()
    last_print = 0
    present_count = 0
    absent_count = 0

    while time.time() - start < duration:
        targets = read_targets(ser)

        now = time.time()
        elapsed = now - start

        if targets:
            present_count += 1
            t = targets[0]
            if now - last_print > 0.5:
                print(f"  [{elapsed:5.1f}s] PRESENT - {t.distance_m:.2f}m away")
                last_print = now
        else:
            absent_count += 1
            if now - last_print > 0.5:
                print(f"  [{elapsed:5.1f}s] ABSENT")
                last_print = now

        time.sleep(0.1)

    print(f"\nPresent: {present_count}, Absent: {absent_count}")
    if present_count > 10 and absent_count > 10:
        print("PASS: Presence detection working")
    elif present_count > 50:
        print("WARN: Always present - try stepping out of view")
    elif absent_count > 50:
        print("WARN: Always absent - check radar positioning")


def run_all_tests(ser: serial.Serial):
    """Run all tests in sequence."""
    print("\n" + "="*60)
    print("RUNNING ALL RADAR TESTS")
    print("="*60)

    if not test_connectivity(ser):
        print("\nStopping - fix connectivity first")
        return

    test_target_tracking(ser, duration=5)

    input("\nPress Enter when ready for breathing test (30s still)...")
    test_breathing(ser, duration=30)

    input("\nPress Enter when ready for movement test (10s still, 10s moving)...")
    test_movement(ser, duration=20)

    input("\nPress Enter when ready for presence test (walk in/out)...")
    test_presence(ser, duration=15)

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LD2450 Radar Test Utility")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--baud", type=int, default=256000, help="Baud rate")
    parser.add_argument("--mode", default="connectivity",
                        choices=["connectivity", "target", "breathing", "movement", "presence", "all"],
                        help="Test mode")
    parser.add_argument("--duration", type=float, default=None, help="Test duration in seconds")
    args = parser.parse_args()

    print(f"Connecting to {args.port} at {args.baud} baud...")

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"ERROR: Could not open {args.port}: {e}")
        sys.exit(1)

    try:
        if args.mode == "connectivity":
            test_connectivity(ser)
        elif args.mode == "target":
            test_target_tracking(ser, args.duration or 5)
        elif args.mode == "breathing":
            test_breathing(ser, args.duration or 30)
        elif args.mode == "movement":
            test_movement(ser, args.duration or 20)
        elif args.mode == "presence":
            test_presence(ser, args.duration or 15)
        elif args.mode == "all":
            run_all_tests(ser)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
