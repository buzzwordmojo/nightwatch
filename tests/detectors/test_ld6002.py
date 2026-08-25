"""
Tests for the HLK-LD6002 vitals radar driver.

Frame bytes here are taken from a real module, not invented.
"""

from __future__ import annotations

import struct

from nightwatch.detectors.radar.ld6002 import (
    RATE_STALE_SECONDS,
    TYPE_HEART_RATE,
    TYPE_PHASE,
    TYPE_RESPIRATION,
    TYPE_TARGET,
    LD6002Driver,
    LD6002Frame,
    LD6002Reading,
)


def frame(ftype: int, payload: bytes) -> bytes:
    """Build a wire frame: 01 | id(2) | len(2 BE) | type(2) | cksum | payload | cksum."""
    return (
        b"\x01" + struct.pack(">H", 0x4EF8) + struct.pack(">H", len(payload))
        + struct.pack(">H", ftype) + b"\x5d" + payload + b"\x00"
    )


# --- framing ---------------------------------------------------------------


def test_parses_a_real_phase_frame():
    d = LD6002Driver("/dev/null")
    d._buf += bytes.fromhex("014ef8000c0a135daf66abbf9e61dc3f614286bf24")
    f = d._pop_frame()
    assert f is not None and f.frame_type == TYPE_PHASE
    assert [round(x, 4) for x in f.floats()] == [-1.3391, 1.7217, -1.0489]


def test_resyncs_past_the_firmware_debug_line():
    """The module emits plaintext between frames; it must not derail framing."""
    d = LD6002Driver("/dev/null")
    d._buf += b"\r\n it's working!!!! \r\n" + frame(TYPE_RESPIRATION, struct.pack("<f", 18.0))
    f = d._pop_frame()
    assert f is not None and f.frame_type == TYPE_RESPIRATION


def test_stray_sof_byte_inside_data_is_skipped():
    d = LD6002Driver("/dev/null")
    d._buf += b"\x01\x01\x01" + frame(TYPE_HEART_RATE, struct.pack("<f", 72.0))
    f = d._pop_frame()
    assert f is not None and f.frame_type == TYPE_HEART_RATE


def test_partial_frame_waits_for_the_rest():
    d = LD6002Driver("/dev/null")
    whole = frame(TYPE_HEART_RATE, struct.pack("<f", 72.0))
    d._buf += whole[:-3]
    assert d._pop_frame() is None
    d._buf += whole[-3:]
    assert d._pop_frame() is not None


def test_unknown_type_is_not_treated_as_a_frame():
    d = LD6002Driver("/dev/null")
    d._buf += frame(0xDEAD, b"\x00\x00\x00\x00") + frame(TYPE_HEART_RATE, struct.pack("<f", 72.0))
    f = d._pop_frame()
    assert f is not None and f.frame_type == TYPE_HEART_RATE


# --- the safety-relevant behaviour -----------------------------------------


def test_out_of_range_sample_does_not_erase_a_good_reading():
    """
    Regression: a placeholder frame used to null the rate.

    Rates arrive sparsely, so nulling on every out-of-range sample left the field
    None most of the time - and an alert rule of the form "respiration_rate < 4
    for 10s" cannot fire against None.
    """
    r = LD6002Reading()
    r.apply(LD6002Frame(1, TYPE_RESPIRATION, struct.pack("<f", 18.0)))
    assert r.respiration_rate == 18.0
    r.apply(LD6002Frame(2, TYPE_RESPIRATION, struct.pack("<f", 0.0)))
    assert r.respiration_rate == 18.0, "a placeholder erased a valid reading"


def test_rate_expires_once_genuinely_stale(monkeypatch):
    """Holding the last value must not mean holding it forever."""
    import nightwatch.detectors.radar.ld6002 as mod

    now = [1000.0]
    monkeypatch.setattr(mod.time, "time", lambda: now[0])

    r = LD6002Reading()
    r.apply(LD6002Frame(1, TYPE_HEART_RATE, struct.pack("<f", 72.0)))
    assert r.heart_rate == 72.0

    now[0] += RATE_STALE_SECONDS + 1
    r.apply(LD6002Frame(2, TYPE_PHASE, struct.pack("<fff", 0.1, 0.2, 0.3)))
    assert r.heart_rate is None, "a stale rate was reported as current"


def test_ranges_reject_physiologically_impossible_values():
    r = LD6002Reading()
    r.apply(LD6002Frame(1, TYPE_HEART_RATE, struct.pack("<f", 900.0)))
    assert r.heart_rate is None
    r.apply(LD6002Frame(2, TYPE_RESPIRATION, struct.pack("<f", 500.0)))
    assert r.respiration_rate is None


def test_waveform_is_bounded():
    """
    50 Hz phase data is held in memory only and must not grow without bound.
    These samples are deliberately never persisted - sustained writes at this
    rate are what destroyed the previous SD card.
    """
    from nightwatch.detectors.radar.ld6002 import WAVEFORM_MAX_SAMPLES

    r = LD6002Reading()
    for i in range(WAVEFORM_MAX_SAMPLES + 400):
        r.apply(LD6002Frame(i, TYPE_PHASE, struct.pack("<fff", 0.0, float(i), 0.0)))
    assert len(r.waveform) == WAVEFORM_MAX_SAMPLES
    assert r.phase_history[-1] == float(WAVEFORM_MAX_SAMPLES + 399)


def test_waveform_since_streams_incrementally():
    """A client should be able to fetch only what it has not already seen."""
    r = LD6002Reading()
    for i in range(10):
        r.apply(LD6002Frame(i, TYPE_PHASE, struct.pack("<fff", 0.0, float(i), 0.0)))
    assert len(r.waveform_since(0)) == 10
    cursor = r.waveform[4][0]
    assert all(w[0] > cursor for w in r.waveform_since(cursor))


def test_target_frame_sets_presence():
    r = LD6002Reading()
    r.apply(LD6002Frame(1, TYPE_TARGET, struct.pack("<i", 1) + struct.pack("<f", 85.68)))
    assert r.target_present is True
    assert round(r.target_value, 2) == 85.68


def test_presence_decays_when_target_frames_stop(monkeypatch):
    """
    With an empty room the module stops sending target frames entirely
    (verified on hardware), so presence must decay on silence - otherwise the
    "Subject not detected" alert can never fire after the person leaves.
    """
    import nightwatch.detectors.radar.ld6002 as mod

    now = [1000.0]
    monkeypatch.setattr(mod.time, "time", lambda: now[0])

    r = LD6002Reading()
    r.apply(LD6002Frame(1, TYPE_TARGET, struct.pack("<i", 1) + struct.pack("<f", 85.0)))
    assert r.target_present is True

    # Empty room: only 0.0-valued rate placeholders keep arriving.
    now[0] += mod.PRESENCE_STALE_SECONDS + 1
    r.apply(LD6002Frame(2, TYPE_RESPIRATION, struct.pack("<f", 0.0)))
    assert r.target_present is False, "presence held forever after target frames stopped"
