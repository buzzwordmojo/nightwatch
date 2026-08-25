"""
HLK-LD6002 60GHz FMCW vitals radar driver.

Unlike the LD2450, which reports target positions and from which respiration has
to be *inferred* by watching sub-millimetre jitter, the LD6002 measures
respiration and heart rate directly and reports them as floats. It also streams
the underlying phase waveforms at 50 Hz, which are useful both for visualisation
and for movement detection.

Wire format, verified against a live module over 1219 frames:

    01 | id(2) | len(2, big-endian) | type(2) | hdr_cksum(1) | payload(len) | cksum(1)

`id` is a rolling frame counter. Payload values are little-endian float32.

    type      rate      payload  meaning
    0x0a13    50 Hz     3 x f32  total / respiratory / heartbeat phase
    0x0a14    ~0.3 Hz   1 x f32  respiration rate, BPM
    0x0a15    ~1.3 Hz   1 x f32  heart rate, BPM
    0x0a16    50 Hz     i32+f32  presence flag + distance-like value

**The baud rate is 1382400 and `stty` cannot set it** - it is not in the standard
termios table, so a shell-configured port silently stays at 115200 and delivers
patterned garbage that looks like a framing bug. pyserial sets it through the
custom-divisor path, which is why this driver opens the port itself.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SOF = 0x01
HEADER_LEN = 8  # SOF + id(2) + len(2) + type(2) + hdr_cksum(1)

TYPE_PHASE = 0x0A13
TYPE_RESPIRATION = 0x0A14
TYPE_HEART_RATE = 0x0A15
TYPE_TARGET = 0x0A16

# Payload length per type. Used to validate framing: without a known checksum
# algorithm, requiring a recognised type at an exact length is what stops a
# stray 0x01 in the data stream from being mistaken for a frame header.
EXPECTED_LEN = {
    TYPE_PHASE: 12,
    TYPE_RESPIRATION: 4,
    TYPE_HEART_RATE: 4,
    TYPE_TARGET: 8,
}

# Ranges the module itself specifies. Values outside these are reported by the
# module while it is still converging and should not be treated as readings.
RESPIRATION_BPM_RANGE = (9.0, 48.0)
HEART_RATE_BPM_RANGE = (60.0, 150.0)

# How long a rate survives without a fresh in-range frame before it is treated
# as unknown. Rates arrive sparsely - respiration roughly every 3s - and the
# module emits out-of-range placeholders while converging. Nulling on every
# placeholder leaves the field None most of the time, and an alert rule of the
# form "respiration_rate < 4 for 10s" can never fire against a None. Holding the
# last good value bounded by this timeout keeps the rule evaluable while still
# reporting genuine loss of signal.
RATE_STALE_SECONDS = 30.0


@dataclass
class LD6002Frame:
    """One parsed frame."""

    frame_id: int
    frame_type: int
    payload: bytes

    def floats(self) -> tuple[float, ...]:
        return struct.unpack("<" + "f" * (len(self.payload) // 4), self.payload)


@dataclass
class LD6002Reading:
    """
    Rolling view of everything the module has told us.

    Rates and phases arrive in separate frames at very different rates, so the
    driver keeps the most recent of each rather than making callers correlate
    them.
    """

    respiration_rate: float | None = None
    heart_rate: float | None = None
    total_phase: float | None = None
    respiration_phase: float | None = None
    heart_phase: float | None = None
    target_present: bool = False
    target_value: float | None = None
    phase_history: list[float] = field(default_factory=list)

    # When each rate was last confirmed by an in-range frame.
    respiration_updated_at: float = 0.0
    heart_rate_updated_at: float = 0.0

    def _expire_stale(self, now: float) -> None:
        if self.respiration_rate is not None and now - self.respiration_updated_at > RATE_STALE_SECONDS:
            self.respiration_rate = None
        if self.heart_rate is not None and now - self.heart_rate_updated_at > RATE_STALE_SECONDS:
            self.heart_rate = None

    def apply(self, frame: LD6002Frame) -> None:
        now = time.time()
        self._expire_stale(now)

        t = frame.frame_type
        if t == TYPE_PHASE:
            total, resp, heart = frame.floats()
            self.total_phase, self.respiration_phase, self.heart_phase = total, resp, heart
            # Bounded history of the respiratory phase, for movement estimation
            # and for the dashboard waveform.
            self.phase_history.append(resp)
            if len(self.phase_history) > 500:  # 10s at 50 Hz
                del self.phase_history[:-500]
        elif t == TYPE_RESPIRATION:
            (v,) = frame.floats()
            lo, hi = RESPIRATION_BPM_RANGE
            if lo <= v <= hi:
                self.respiration_rate = v
                self.respiration_updated_at = now
            # else: keep the previous value; _expire_stale retires it in time
        elif t == TYPE_HEART_RATE:
            (v,) = frame.floats()
            lo, hi = HEART_RATE_BPM_RANGE
            if lo <= v <= hi:
                self.heart_rate = v
                self.heart_rate_updated_at = now
        elif t == TYPE_TARGET:
            flag = struct.unpack("<i", frame.payload[:4])[0]
            (val,) = struct.unpack("<f", frame.payload[4:])
            self.target_present = bool(flag)
            self.target_value = val


class LD6002Driver:
    """Serial driver for the HLK-LD6002."""

    DEFAULT_BAUD = 1382400

    def __init__(self, port: str, baud_rate: int = DEFAULT_BAUD, timeout: float = 1.0):
        self._port = port
        self._baud = baud_rate
        self._timeout = timeout
        self._serial = None
        self._buf = bytearray()

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    async def connect(self) -> None:
        try:
            import serial
        except ImportError as e:
            raise ConnectionError("pyserial not installed. Run: pip install pyserial") from e

        try:
            self._serial = await asyncio.to_thread(
                serial.Serial, self._port, self._baud, timeout=self._timeout
            )
        except Exception as e:
            raise ConnectionError(f"Failed to open {self._port} at {self._baud}: {e}") from e

        self._serial.reset_input_buffer()
        self._buf.clear()
        logger.info("LD6002 connected on %s at %d baud", self._port, self._baud)

    async def disconnect(self) -> None:
        if self._serial is not None:
            try:
                await asyncio.to_thread(self._serial.close)
            finally:
                self._serial = None
        self._buf.clear()

    def _pop_frame(self) -> LD6002Frame | None:
        """Take one valid frame off the front of the buffer, resyncing as needed."""
        buf = self._buf
        while True:
            start = buf.find(bytes([SOF]))
            if start < 0:
                # Keep nothing; there is no partial header worth preserving.
                buf.clear()
                return None
            if start:
                del buf[:start]
            if len(buf) < HEADER_LEN:
                return None

            length = struct.unpack(">H", buf[3:5])[0]
            ftype = struct.unpack(">H", buf[5:7])[0]

            if EXPECTED_LEN.get(ftype) != length:
                # Not a real header - a 0x01 inside a payload or a debug line.
                del buf[:1]
                continue

            total = HEADER_LEN + length + 1
            if len(buf) < total:
                return None  # wait for the rest

            frame = LD6002Frame(
                frame_id=struct.unpack(">H", buf[1:3])[0],
                frame_type=ftype,
                payload=bytes(buf[HEADER_LEN:HEADER_LEN + length]),
            )
            del buf[:total]
            return frame

    async def read_frames(self) -> AsyncIterator[LD6002Frame]:
        """Yield frames until disconnected."""
        if self._serial is None:
            raise RuntimeError("Not connected")

        while self.is_connected:
            try:
                waiting = self._serial.in_waiting or 1
                chunk = await asyncio.to_thread(self._serial.read, waiting)
            except Exception as e:
                logger.error("LD6002 read failed: %s", e)
                raise

            if chunk:
                self._buf += chunk
                # Runaway guard: without a valid frame the buffer must not grow
                # without bound.
                if len(self._buf) > 8192:
                    logger.warning("LD6002 buffer overflow, resyncing")
                    del self._buf[:-1024]
                while (frame := self._pop_frame()) is not None:
                    yield frame
            else:
                await asyncio.sleep(0.01)
