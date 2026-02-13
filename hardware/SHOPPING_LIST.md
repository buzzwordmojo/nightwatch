# Nightwatch Shopping List

Complete parts list for building the Nightwatch monitoring system.

**Last Updated:** February 2025

---

## Quick Summary

| Phase | Components | Estimated Cost |
|-------|------------|----------------|
| Core Platform | Pi 5, power, SD card, case | ~$96 |
| Phase 1: Radar | LD2450, USB-C adapter, USB cable, wires | ~$39 |
| Phase 2: Audio | Lavalier mic + gooseneck mount | ~$30 |
| Phase 3: BCG | Piezo, amp, ADC | ~$45 |
| Notifications | Speaker, buzzer | ~$15 |
| **Total** | | **~$225** |

---

## Core Platform (Required)

### Raspberry Pi 5

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Raspberry Pi 5 4GB** | Main computer | $60 | [Adafruit](https://www.adafruit.com/product/5812) |
| | | | [Amazon](https://www.amazon.com/dp/B0CK3L9WD3) |

**Note:** 4GB is sufficient. 8GB only needed if you plan heavy ML processing.

### Power Supply

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Official Pi 5 PSU (27W)** | 5V/5A USB-C | $12 | [Adafruit](https://www.adafruit.com/product/5814) |

**Important:** The Pi 5 needs more power than previous models. Use the official 27W supply for reliable operation.

### Storage

| Item | Spec | Price | Link |
|------|------|-------|------|
| **MicroSD Card 32GB+** | Class 10 / A2 | $10-15 | [Samsung EVO Select 64GB (2024)](https://www.amazon.com/dp/B0CWPNFH9M) |
| | | | [SanDisk Extreme 64GB](https://www.amazon.com/dp/B09X7BK27V) |

**Tip:** Get at least 32GB. 64GB gives room for recording data.

### Case

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Pi 5 Case with Fan** | Active cooling | $10-15 | [Argon ONE V3](https://www.amazon.com/dp/B0CNGSXGT2) |
| **OR: 3D Print** | Custom design | $0 | STL files in `/hardware/3d_prints/` |

---

## Phase 1: Radar Sensor

### HLK-LD2450 Radar Module

| Item | Spec | Price | Link |
|------|------|-------|------|
| **HLK-LD2450** | 24GHz mmWave radar | $15-20 | [Amazon (Ruitutedianzi)](https://www.amazon.com/dp/B0DP6QLQZV) |
| | Multi-target tracking | | [Amazon (ZORZA)](https://www.amazon.com/dp/B0D46LY4P8) |
| | UART output | | |

**Alternative:** HLK-LD2410C ($12-15) - Simpler but less features

### USB-to-UART Adapter (Remote Mounting)

Allows the radar to be wall-mounted away from the Pi with just a USB cable.

| Item | Spec | Price | Link |
|------|------|-------|------|
| **CP2102 USB-C to TTL** | 3.3V/5V switchable, USB-C port | $8 | [Amazon XICOOLEE](https://www.amazon.com/dp/B0C8RRDCXB) |
| **USB-A to USB-C Cable** | 10ft, for wall-mounted radar | $8 | [Amazon 10ft](https://www.amazon.com/dp/B01LONPOV2) |
| | (or use any long USB-C cable you have) | | |

**Wiring (Radar to CP2102):**
```
LD2450      CP2102
──────      ──────
VCC   ───>  5V (or 3.3V)
GND   ───>  GND
TX    ───>  RX
RX    <───  TX
```

### Short Wiring (Radar to CP2102)

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Dupont Jumper Wires** | Female-Female, 10-20cm | $3-5 | [Amazon](https://www.amazon.com/dp/B01EV70C78) |
| **JST Connector Kit** | Optional, cleaner | $8 | [Amazon](https://www.amazon.com/dp/B01MCZE2HM) |

### Wall Mount Enclosure

| Item | Spec | Price | Link |
|------|------|-------|------|
| **3D Printed Mount** | Holds radar + CP2102 | $0 | STL in `/hardware/3d_prints/` |
| **OR: Small Project Box** | 80x50x25mm | $3-5 | [Amazon](https://www.amazon.com/dp/B07Q14K8YT) |
| **Mounting Tape** | 3M VHB or Command strips | $5 | [3M VHB](https://www.amazon.com/dp/B00004Z4BV) |
| **Drywall Anchors** | For screw mounting | $4 | [Amazon](https://www.amazon.com/dp/B0B8F4ZJ61) |

---

## Phase 2: Audio Sensor

### USB Microphone

| Item | Spec | Price | Link |
|------|------|-------|------|
| **FIFINE K053 Lavalier** | Cardioid, clip-on, small | $16 | [Amazon](https://www.amazon.com/dp/B077VNGVL2) |
| **Gooseneck Clamp Mount** | Flexible arm for aiming mic | $14 | [Amazon Tryone](https://www.amazon.com/dp/B0777JP14F) |

**Recommended:** FIFINE K053 - cardioid pattern rejects sound from sides (important with multiple people in room). Mount on gooseneck clamp and aim at bed.

**Tip:** You may need to 3D print a small adapter to hold the lavalier capsule on the gooseneck arm.

---

## Phase 3: BCG Bed Sensor

### Option A: Piezo Film Sensor (Recommended)

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Large Piezo Film** | PVDF, 100mm+ | $15-25 | [SparkFun Piezo](https://www.sparkfun.com/products/10293) |
| **Piezo Element (Disc)** | 35mm disc (simpler) | $3-5 | [Amazon 20-pack](https://www.amazon.com/dp/B01N5HN94S) |
| | | | [Amazon DZS Elec 15-pack](https://www.amazon.com/dp/B084KHH7B6) |

**Note:** Large film sensors work better but cost more. Start with disc for testing.

### Signal Conditioning

| Item | Spec | Price | Link |
|------|------|-------|------|
| **MCP3008 ADC** | 8-ch 10-bit SPI ADC | $4 | [Adafruit](https://www.adafruit.com/product/856) |
| | | | [Amazon 4-pack](https://www.amazon.com/dp/B01HGCSGXM) |
| **LM358 Op-Amp** | Dual op-amp | $1 | [Amazon 10-pack](https://www.amazon.com/dp/B07WQWPLSP) |
| **Resistors** | Assorted kit | $8 | [Amazon](https://www.amazon.com/dp/B08FD1XVL6) |
| **Capacitors** | Assorted ceramic | $8 | [Amazon](https://www.amazon.com/dp/B07PP7SFY3) |
| **Breadboard** | For prototyping | $5 | [Amazon](https://www.amazon.com/dp/B082KBF7MM) |
| **OR: Breakout Board** | Pre-built amp | $15 | See below |

### Pre-Built Amplifier Options

| Item | Spec | Price | Link |
|------|------|-------|------|
| **SparkFun OpAmp Breakout** | LMV358 | $5 | [SparkFun](https://www.sparkfun.com/products/9816) |
| **Adafruit MAX9814** | Mic amp with AGC | $8 | [Adafruit](https://www.adafruit.com/product/1713) |

### Option B: Load Cells Under Bed

| Item | Spec | Price | Link |
|------|------|-------|------|
| **50kg Load Cell x4** | Strain gauge + HX711 | $15 | [Amazon Geekstory Kit](https://www.amazon.com/dp/B079FTXR7Y) |
| **HX711 ADC** | 24-bit load cell ADC | $5 | [Amazon 2-pack](https://www.amazon.com/dp/B07MTYT95R) |

**Note:** More complex to install but very accurate.

### Mounting Materials

| Item | Spec | Price | Link |
|------|------|-------|------|
| **Foam Padding** | To isolate sensor | $5 | Craft store |
| **Double-sided Tape** | Secure to bed frame | $5 | [Amazon](https://www.amazon.com/dp/B00347A8GC) |

---

## Notification Hardware

### Local Alarm

| Item | Spec | Price | Link |
|------|------|-------|------|
| **USB Speaker** | Powered, 3W+ | $10-15 | [Amazon](https://www.amazon.com/dp/B075M7FHM1) |
| **OR: GPIO Buzzer** | Active buzzer, 5V | $3 | [Amazon 5-pack](https://www.amazon.com/dp/B07KJHQPJF) |
| **Piezo Buzzer** | Loud, 90dB+ | $2 | [Adafruit](https://www.adafruit.com/product/160) |

### Visual Alert (Optional)

| Item | Spec | Price | Link |
|------|------|-------|------|
| **LED Strip** | WS2812B, 1m | $10 | [Amazon](https://www.amazon.com/dp/B01CDTEJBG) |
| **Red LED** | 5mm, bright | $3 | [Amazon 100-pack](https://www.amazon.com/dp/B0739RYXVC) |

---

## Tools & Supplies

### If You Don't Have These

| Item | Price | Link |
|------|-------|------|
| Soldering iron + solder | $20 | [Amazon](https://www.amazon.com/dp/B08R3515SF) |
| Wire strippers | $8 | [Amazon](https://www.amazon.com/dp/B000JNNWQ2) |
| Multimeter | $15 | [Amazon](https://www.amazon.com/dp/B01ISAMUA6) |
| Heat shrink tubing | $8 | [Amazon](https://www.amazon.com/dp/B084GDLSCK) |
| Electrical tape | $5 | [Amazon](https://www.amazon.com/dp/B00004WCCP) |

---

## 3D Printing Files Needed

Files will be in `/hardware/3d_prints/`:

| File | Description | Print Time |
|------|-------------|------------|
| `radar_wall_enclosure.stl` | Wall enclosure for LD2450 + CP2102 | ~3 hours |
| `radar_wall_enclosure_lid.stl` | Snap-fit lid | ~1 hour |
| `radar_mount_ceiling.stl` | Ceiling mount variant | ~2 hours |
| `pi_case.stl` | Custom Pi 5 enclosure | ~4 hours |
| `mic_bracket.stl` | Microphone mounting arm | ~1 hour |
| `cable_clips.stl` | Cable management | ~30 min |

**Materials:** PLA or PETG, 0.2mm layer height, 20% infill

---

## Shopping by Phase

### Phase 1 Order (~$135)
*Get monitoring working with radar*

- [ ] Raspberry Pi 5 (4GB) - $60
- [ ] Official 27W Power Supply - $12
- [ ] MicroSD Card 64GB - $12
- [ ] Pi 5 Case with Fan - $12
- [ ] HLK-LD2450 Radar - $18
- [ ] CP2102 USB-C to TTL Adapter - $8
- [ ] USB-A to USB-C Cable (10ft) - $8
- [ ] Dupont Jumper Wires - $5

### Phase 2 Add-on ($30)
*Add audio for redundancy*

- [ ] FIFINE K053 Lavalier Mic - $16
- [ ] Gooseneck Clamp Mount - $14

### Phase 3 Add-on ($45)
*Add BCG for accurate heart rate*

- [ ] Piezo Element (start with disc) - $5
- [ ] MCP3008 ADC - $5
- [ ] SparkFun OpAmp Breakout - $5
- [ ] Resistors/Capacitors kit - $15
- [ ] Breadboard - $5
- [ ] Larger Piezo Film (upgrade later) - $15

### Notifications ($15)
*Can add anytime*

- [ ] USB Speaker - $12
- [ ] GPIO Buzzer (backup) - $3

---

## Supplier Notes

### Fast Shipping (US)
- **Amazon** - 1-2 day Prime
- **Adafruit** - 3-5 days, great quality
- **SparkFun** - 3-5 days, good documentation
- **Digi-Key** - 1-2 days, industrial parts

### Budget Option (Slower)
- **AliExpress** - 2-4 weeks, much cheaper
- Best for: LD2450, piezo elements, components
- Order early to have parts ready

### Local Options
- **Micro Center** - If you have one nearby
- **Fry's** - Limited locations remain
- **Electronics stores** - For basic components

---

## What to Order First

**Minimum Viable System** (order today):

1. Raspberry Pi 5 4GB - $60
2. 27W Power Supply - $12
3. 64GB MicroSD Card - $12
4. HLK-LD2450 Radar - $18
5. CP2102 USB-C to TTL adapter - $8
6. USB-A to USB-C cable (10ft) - $8
7. Dupont wires - $5

**Total: ~$123**

This gets you a working radar-based monitoring system with proper wall mounting capability. Add audio and BCG as budget allows.

**3D Print:** Radar wall enclosure (see `/hardware/3d_prints/DESIGN_SPECS.md`)

---

## Notes for Miles

Given Miles is 13 and ~85 lbs:

- **Radar distance**: 1-1.5m should work well
- **BCG sensor**: Single large piezo under torso area
- **Audio**: Standard placement 0.5-1m from head
- **No contact sensors needed**: All sensing is remote

The system should detect his breathing and movement patterns reliably with just the radar. Audio and BCG add redundancy and heart rate accuracy.
