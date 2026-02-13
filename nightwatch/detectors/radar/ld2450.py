"""
HLK-LD2450 mmWave Radar Driver.

The LD2450 is a 24GHz mmWave radar module that can detect:
- Multiple targets (up to 3)
- Position (X, Y coordinates in mm)
- Speed (cm/s)
- Micro-movements (breathing, heartbeat)

Communication: UART at 256000 baud
Protocol: Binary frames with header/footer markers

Reference: https://github.com/csRon/HLK-LD2450
"""

from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass
from typing import AsyncIterator

import serial_asyncio


# Frame markers
FRAME_HEADER = bytes([0xAA, 0xFF, 0x03, 0x00])
FRAME_FOOTER = bytes([0x55, 0xCC])

# Command frame markers
CMD_HEADER = bytes([0xFD, 0xFC, 0xFB, 0xFA])
CMD_FOOTER = bytes([0x04, 0x03, 0x02, 0x01])


@dataclass
class LD2450Target:
    """Single detected target from LD2450."""

    x: int  # X position in mm (horizontal, -ve = left, +ve = right)
    y: int  # Y position in mm (depth, always positive)
    speed: int  # Speed in cm/s (signed, +ve = approaching, -ve = receding)
    resolution: int  # Detection resolution (internal)

    @property
    def distance_mm(self) -> float:
        """Calculate distance from sensor in mm."""
        return (self.x**2 + self.y**2) ** 0.5

    @property
    def distance_m(self) -> float:
        """Calculate distance from sensor in meters."""
        return self.distance_mm / 1000.0

    @property
    def angle_degrees(self) -> float:
        """Calculate angle from center in degrees."""
        import math

        if self.y == 0:
            return 90.0 if self.x > 0 else -90.0
        return math.degrees(math.atan2(self.x, self.y))

    @property
    def is_valid(self) -> bool:
        """Check if target data is valid (not zero/placeholder)."""
        return not (self.x == 0 and self.y == 0 and self.speed == 0)


@dataclass
class LD2450Frame:
    """Parsed data frame from LD2450."""

    targets: list[LD2450Target]
    raw_data: bytes

    @classmethod
    def parse(cls, data: bytes) -> LD2450Frame | None:
        """
        Parse raw frame data into LD2450Frame.

        Frame format (26 bytes total):
        - Header: 4 bytes (0xAA, 0xFF, 0x03, 0x00)
        - Target 1: 8 bytes
        - Target 2: 8 bytes
        - Target 3: 8 bytes
        - Footer: 2 bytes (0x55, 0xCC)

        Target format (8 bytes):
        - X position: 2 bytes (signed int16, little-endian)
        - Y position: 2 bytes (signed int16, little-endian)
        - Speed: 2 bytes (signed int16, little-endian)
        - Resolution: 2 bytes (uint16, little-endian)
        """
        if len(data) < 30:
            return None

        # Find frame in data
        header_idx = data.find(FRAME_HEADER)
        if header_idx == -1:
            return None

        frame_data = data[header_idx : header_idx + 30]
        if len(frame_data) < 30:
            return None

        # Verify footer
        if frame_data[28:30] != FRAME_FOOTER:
            return None

        targets = []

        # Parse 3 targets
        for i in range(3):
            offset = 4 + (i * 8)
            target_data = frame_data[offset : offset + 8]

            # Unpack little-endian: 2x signed int16, 1x signed int16, 1x uint16
            x, y, speed, resolution = struct.unpack("<hhhH", target_data)

            # The sensor uses a sign bit in the high bit for X and Y
            # X: bit 15 = sign (0=positive, 1=negative), bits 0-14 = magnitude
            # Y: same format
            if x & 0x8000:
                x = -(x & 0x7FFF)
            if y & 0x8000:
                y = -(y & 0x7FFF)

            target = LD2450Target(x=x, y=y, speed=speed, resolution=resolution)
            if target.is_valid:
                targets.append(target)

        return cls(targets=targets, raw_data=frame_data)


class LD2450Driver:
    """
    Async serial driver for HLK-LD2450 mmWave radar.

    Usage:
        driver = LD2450Driver("/dev/ttyAMA0")
        await driver.connect()

        async for frame in driver.read_frames():
            for target in frame.targets:
                print(f"Target at {target.distance_m:.2f}m")

        await driver.disconnect()
    """

    def __init__(
        self,
        port: str = "/dev/ttyAMA0",
        baud_rate: int = 256000,
    ):
        self._port = port
        self._baud_rate = baud_rate
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Open serial connection to radar."""
        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self._port,
            baudrate=self._baud_rate,
        )
        self._connected = True

    async def disconnect(self) -> None:
        """Close serial connection."""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._connected = False

    async def read_frame(self) -> LD2450Frame | None:
        """
        Read and parse a single frame from the radar.

        Returns None if no valid frame could be read.
        """
        if not self._reader:
            raise RuntimeError("Not connected")

        # Read enough bytes for a frame
        try:
            data = await asyncio.wait_for(self._reader.read(64), timeout=1.0)
        except asyncio.TimeoutError:
            return None

        if not data:
            return None

        return LD2450Frame.parse(data)

    async def read_frames(self) -> AsyncIterator[LD2450Frame]:
        """
        Continuously read frames from the radar.

        Yields LD2450Frame objects as they are received.
        """
        if not self._reader:
            raise RuntimeError("Not connected")

        buffer = bytearray()

        while self._connected:
            try:
                # Read available data
                data = await asyncio.wait_for(self._reader.read(256), timeout=0.5)
                if not data:
                    continue

                buffer.extend(data)

                # Process all complete frames in buffer
                while len(buffer) >= 30:
                    # Find frame header
                    header_idx = buffer.find(FRAME_HEADER)

                    if header_idx == -1:
                        # No header found, keep last few bytes in case header is split
                        buffer = buffer[-3:]
                        break

                    if header_idx > 0:
                        # Discard data before header
                        buffer = buffer[header_idx:]

                    if len(buffer) < 30:
                        # Not enough data for complete frame
                        break

                    # Try to parse frame
                    frame = LD2450Frame.parse(bytes(buffer[:30]))

                    if frame:
                        yield frame
                        buffer = buffer[30:]
                    else:
                        # Invalid frame, skip header and try again
                        buffer = buffer[4:]

            except asyncio.TimeoutError:
                continue
            except Exception:
                if self._connected:
                    raise
                break

    async def send_command(self, cmd: bytes) -> bytes:
        """
        Send a command and read response.

        Commands are wrapped in CMD_HEADER and CMD_FOOTER.
        """
        if not self._writer or not self._reader:
            raise RuntimeError("Not connected")

        # Build command frame
        frame = CMD_HEADER + cmd + CMD_FOOTER
        self._writer.write(frame)
        await self._writer.drain()

        # Read response
        try:
            response = await asyncio.wait_for(self._reader.read(256), timeout=1.0)
            return response
        except asyncio.TimeoutError:
            return b""

    async def enable_config_mode(self) -> bool:
        """Enable configuration mode."""
        cmd = bytes([0x04, 0x00, 0xFF, 0x00, 0x01, 0x00])
        response = await self.send_command(cmd)
        return len(response) > 0

    async def disable_config_mode(self) -> bool:
        """Disable configuration mode (return to normal operation)."""
        cmd = bytes([0x04, 0x00, 0xFE, 0x00])
        response = await self.send_command(cmd)
        return len(response) > 0

    async def set_detection_area(
        self,
        x_min: int = -4000,
        x_max: int = 4000,
        y_min: int = 0,
        y_max: int = 6000,
    ) -> bool:
        """
        Set detection area boundaries.

        Args:
            x_min: Minimum X in mm (default -4000, left side)
            x_max: Maximum X in mm (default 4000, right side)
            y_min: Minimum Y in mm (default 0, closest)
            y_max: Maximum Y in mm (default 6000, farthest)
        """
        await self.enable_config_mode()

        # Command to set region
        cmd = struct.pack("<HHHhhhh", 0x0007, 0x0001, 0x0000, x_min, y_min, x_max, y_max)
        response = await self.send_command(cmd)

        await self.disable_config_mode()
        return len(response) > 0

    async def get_version(self) -> str:
        """Get firmware version string."""
        await self.enable_config_mode()

        cmd = bytes([0x02, 0x00, 0x00, 0x00])
        response = await self.send_command(cmd)

        await self.disable_config_mode()

        # Parse version from response
        if len(response) > 10:
            try:
                # Version is typically in bytes 8-12
                return response[8:12].decode("ascii", errors="ignore")
            except Exception:
                pass
        return "unknown"
