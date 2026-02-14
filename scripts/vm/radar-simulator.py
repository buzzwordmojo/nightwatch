#!/usr/bin/env python3
"""
Radar simulator for Nightwatch testing.

Generates realistic LD2450 radar frames and sends them to a virtual
serial port, simulating a sleeping child's breathing and movement.

Usage:
    ./scripts/vm/radar-simulator.py [--scenario SCENARIO] [--port PORT]

Scenarios:
    normal      - Normal sleep with regular breathing (default)
    apnea       - Breathing stops for 15 seconds
    tachypnea   - Rapid breathing (>25 BPM)
    movement    - Restless movement
    seizure     - Seizure-like rapid movements
    empty       - Empty bed (no target detected)

Example:
    # Start normal breathing simulation
    ./scripts/vm/radar-simulator.py

    # Simulate an apnea event
    ./scripts/vm/radar-simulator.py --scenario apnea
"""

from __future__ import annotations

import argparse
import math
import random
import struct
import sys
import time
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Target:
    """A detected target with position and velocity."""

    x: int  # mm, horizontal position
    y: int  # mm, distance from sensor
    speed: int  # mm/s, radial velocity


def create_ld2450_frame(targets: list[Target]) -> bytes:
    """
    Create a valid LD2450 data frame.

    Frame format:
    - Header: 0xAA 0xFF 0x03 0x00 (4 bytes)
    - Target 1: x(2) + y(2) + speed(2) = 6 bytes
    - Target 2: x(2) + y(2) + speed(2) = 6 bytes
    - Target 3: x(2) + y(2) + speed(2) = 6 bytes
    - Footer: 0x55 0xCC (2 bytes)
    Total: 26 bytes
    """
    # Frame header
    frame = bytes([0xAA, 0xFF, 0x03, 0x00])

    # Up to 3 targets
    for i in range(3):
        if i < len(targets):
            t = targets[i]
            frame += struct.pack("<hhh", t.x, t.y, t.speed)
        else:
            # Empty target slot
            frame += bytes([0x00] * 6)

    # Frame footer
    frame += bytes([0x55, 0xCC])

    return frame


class BreathingSimulator:
    """Simulates breathing motion patterns."""

    def __init__(
        self,
        base_y: int = 1500,  # 1.5m from sensor
        breath_rate_bpm: float = 14.0,  # breaths per minute
        breath_amplitude: float = 7.0,  # mm chest movement
    ):
        self.base_y = base_y
        self.breath_rate = breath_rate_bpm / 60.0  # Hz
        self.breath_amplitude = breath_amplitude
        self.start_time = time.time()

        # Add natural variation
        self._rate_variation = random.uniform(-0.02, 0.02)
        self._amp_variation = random.uniform(-1, 1)

    def get_position(self) -> Target:
        """Get current target position with breathing motion."""
        t = time.time() - self.start_time

        # Breathing motion (sinusoidal)
        rate = self.breath_rate + self._rate_variation
        amp = self.breath_amplitude + self._amp_variation
        breath_offset = amp * math.sin(2 * math.pi * rate * t)

        # Small random noise (micro-movements)
        noise_x = random.gauss(0, 2)
        noise_y = random.gauss(0, 1)

        # Speed based on breathing phase (derivative of position)
        speed = int(amp * 2 * math.pi * rate * math.cos(2 * math.pi * rate * t))

        return Target(
            x=int(noise_x),
            y=int(self.base_y + breath_offset + noise_y),
            speed=speed,
        )


def scenario_normal() -> Iterator[list[Target]]:
    """Normal sleep breathing pattern."""
    sim = BreathingSimulator(breath_rate_bpm=14.0)
    while True:
        yield [sim.get_position()]


def scenario_apnea() -> Iterator[list[Target]]:
    """
    Apnea event: normal breathing, then stops for 15 seconds.

    Timeline:
    - 0-30s: Normal breathing
    - 30-45s: APNEA (no movement)
    - 45s+: Breathing resumes
    """
    sim = BreathingSimulator(breath_rate_bpm=14.0)
    start_time = time.time()
    apnea_start = 30.0
    apnea_duration = 15.0

    while True:
        elapsed = time.time() - start_time

        if apnea_start <= elapsed < (apnea_start + apnea_duration):
            # During apnea - static position
            yield [Target(x=0, y=1500, speed=0)]
        else:
            # Normal breathing
            yield [sim.get_position()]


def scenario_tachypnea() -> Iterator[list[Target]]:
    """Rapid breathing (>25 BPM) - could indicate distress."""
    sim = BreathingSimulator(breath_rate_bpm=28.0, breath_amplitude=10.0)
    while True:
        yield [sim.get_position()]


def scenario_movement() -> Iterator[list[Target]]:
    """Restless movement with position changes."""
    base_sim = BreathingSimulator(breath_rate_bpm=14.0)
    start_time = time.time()
    last_shift_time = start_time
    position_offset_x = 0
    position_offset_y = 0

    while True:
        elapsed = time.time() - start_time
        since_shift = time.time() - last_shift_time

        # Random position shifts every 5-15 seconds
        if since_shift > random.uniform(5, 15):
            position_offset_x = random.randint(-200, 200)
            position_offset_y = random.randint(-100, 100)
            last_shift_time = time.time()

        pos = base_sim.get_position()
        yield [
            Target(
                x=pos.x + position_offset_x,
                y=pos.y + position_offset_y,
                speed=pos.speed + random.randint(-50, 50),
            )
        ]


def scenario_seizure() -> Iterator[list[Target]]:
    """
    Seizure-like rapid, irregular movements.

    Timeline:
    - 0-20s: Normal sleep
    - 20-35s: Seizure activity (rapid shaking)
    - 35s+: Post-ictal (very still)
    """
    normal_sim = BreathingSimulator(breath_rate_bpm=14.0)
    start_time = time.time()
    seizure_start = 20.0
    seizure_duration = 15.0

    while True:
        elapsed = time.time() - start_time

        if seizure_start <= elapsed < (seizure_start + seizure_duration):
            # During seizure - rapid, chaotic movement
            shake_freq = random.uniform(3, 8)  # Hz
            amplitude = random.uniform(30, 80)
            phase = elapsed * 2 * math.pi * shake_freq

            yield [
                Target(
                    x=int(amplitude * math.sin(phase) + random.gauss(0, 20)),
                    y=int(1500 + amplitude * math.cos(phase * 1.3) + random.gauss(0, 10)),
                    speed=random.randint(-500, 500),
                )
            ]
        elif elapsed >= (seizure_start + seizure_duration):
            # Post-ictal - very still, slow breathing
            yield [Target(x=0, y=1500, speed=0)]
        else:
            # Normal pre-seizure
            yield [normal_sim.get_position()]


def scenario_empty() -> Iterator[list[Target]]:
    """Empty bed - no targets detected."""
    while True:
        yield []


SCENARIOS = {
    "normal": scenario_normal,
    "apnea": scenario_apnea,
    "tachypnea": scenario_tachypnea,
    "movement": scenario_movement,
    "seizure": scenario_seizure,
    "empty": scenario_empty,
}


def main():
    parser = argparse.ArgumentParser(
        description="Simulate LD2450 radar data for Nightwatch testing"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        choices=list(SCENARIOS.keys()),
        default="normal",
        help="Simulation scenario (default: normal)",
    )
    parser.add_argument(
        "--port",
        "-p",
        default="/tmp/ttyRADAR_SIM",
        help="Serial port to write to (default: /tmp/ttyRADAR_SIM)",
    )
    parser.add_argument(
        "--rate",
        "-r",
        type=int,
        default=20,
        help="Update rate in Hz (default: 20)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=0,
        help="Duration in seconds (0 = infinite, default: 0)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print frames to stdout instead of serial port",
    )

    args = parser.parse_args()

    # Get scenario generator
    scenario_fn = SCENARIOS[args.scenario]
    scenario = scenario_fn()

    print(f"Radar Simulator")
    print(f"===============")
    print(f"Scenario: {args.scenario}")
    print(f"Port: {args.port}")
    print(f"Rate: {args.rate} Hz")
    print(f"")

    # Open serial port
    port = None
    if not args.stdout:
        try:
            import serial

            port = serial.Serial(args.port, 256000, timeout=1)
            print(f"Connected to {args.port}")
        except ImportError:
            print("WARNING: pyserial not installed, using stdout")
            args.stdout = True
        except Exception as e:
            print(f"WARNING: Could not open {args.port}: {e}")
            print("Using stdout instead")
            args.stdout = True

    print(f"")
    print(f"Sending frames... (Ctrl+C to stop)")
    print(f"")

    start_time = time.time()
    frame_count = 0
    interval = 1.0 / args.rate

    try:
        while True:
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                break

            # Get next frame
            targets = next(scenario)
            frame = create_ld2450_frame(targets)

            # Send frame
            if args.stdout:
                # Print hex representation
                hex_str = " ".join(f"{b:02x}" for b in frame)
                if targets:
                    t = targets[0]
                    print(f"[{frame_count:6d}] x={t.x:+5d} y={t.y:5d} v={t.speed:+4d} | {hex_str}")
                else:
                    print(f"[{frame_count:6d}] (no target) | {hex_str}")
            else:
                port.write(frame)

            frame_count += 1

            # Rate limiting
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\nStopped after {frame_count} frames")

    finally:
        if port:
            port.close()


if __name__ == "__main__":
    main()
