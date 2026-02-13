# 3D Print Design Specifications

Design specs for Nightwatch 3D printed enclosures and mounts.

---

## Radar Wall Enclosure

Houses the LD2450 radar module and CP2102 USB-to-UART adapter in a single wall-mounted unit.

### Components to Fit

| Component | Dimensions (mm) | Notes |
|-----------|-----------------|-------|
| HLK-LD2450 | 24 x 30 x 8 | Radar module |
| CP2102 board | 25 x 15 x 5 | USB-to-TTL adapter |
| Wiring | 4 wires | ~5cm between boards |
| USB cable exit | 12mm diameter | Strain relief needed |

### Design Requirements

```
       FRONT VIEW                    SIDE VIEW (wall mount)
    ┌─────────────────┐              ┌──────┐
    │  ┌───────────┐  │              │      │╲ 45° angle
    │  │  LD2450   │  │  ← radar     │LD2450│ ╲
    │  │  (front)  │  │    window    │      │  ╲
    │  └───────────┘  │              ├──────┤   │
    │                 │              │CP2102│   │
    │  ┌─────────┐    │              │      │   │
    │  │ CP2102  │    │              └──┬───┘   │
    │  └─────────┘    │                 │ USB   │
    │        ○        │  ← USB exit     │ cable │
    └─────────────────┘                 ▼       │
                                              WALL
```

### Dimensions

| Measurement | Value | Notes |
|-------------|-------|-------|
| **Outer Width** | 50mm | Compact profile |
| **Outer Height** | 70mm | Fits both boards |
| **Outer Depth** | 30mm | At deepest point |
| **Wall Thickness** | 2mm | Standard |
| **Radar Window** | 28 x 34mm | Cutout for radar face |
| **Tilt Angle** | 45° | Points down at bed |
| **Mount Holes** | 2x, 4mm dia | For screws or keyhole |
| **USB Exit** | 12mm dia | Bottom, with strain relief |

### Features

1. **Radar window**: Open front for radar signal (RF transparent)
2. **45° tilt**: Built into enclosure so radar points down when wall-mounted
3. **Snap-fit lid**: Easy access for maintenance
4. **Cable channel**: Internal routing from CP2102 to USB exit
5. **Ventilation slots**: Small slots for airflow (electronics heat)
6. **Mounting options**:
   - Keyhole slots for screw mounting
   - Flat back for 3M VHB tape

### Assembly

```
1. Solder/connect wires:
   LD2450 VCC  ──> CP2102 5V
   LD2450 GND  ──> CP2102 GND
   LD2450 TX   ──> CP2102 RX
   LD2450 RX   ──> CP2102 TX

2. Place LD2450 in upper compartment (face toward window)

3. Place CP2102 in lower compartment (USB port toward exit hole)

4. Route USB cable through exit hole

5. Snap lid closed

6. Mount to wall with screws or tape
```

### Print Settings

| Setting | Value |
|---------|-------|
| Material | PETG (preferred) or PLA |
| Layer Height | 0.2mm |
| Infill | 20% |
| Supports | Yes (for angled sections) |
| Orientation | Flat back on bed |

---

## Radar Ceiling Mount (Alternative)

For ceiling mounting directly above bed.

### Design Requirements

```
    CEILING
    ════════════════════════════
         │ mounting plate
         │
    ┌────┴────┐
    │ LD2450  │  ← radar faces down
    │ CP2102  │
    └────┬────┘
         │ USB cable
         ▼
```

### Dimensions

| Measurement | Value |
|-------------|-------|
| Outer diameter | 60mm (round) |
| Height | 25mm |
| Cable exit | Side, 12mm |

### Features

- Flush ceiling mount
- Radar faces straight down
- Clean single-cable look

---

## Pi 5 Nightstand Case

Main enclosure for Raspberry Pi 5 on nightstand.

### Components to Fit

| Component | Notes |
|-----------|-------|
| Raspberry Pi 5 | 85 x 56mm board |
| Active cooler fan | Optional, top mount |
| GPIO access | For BCG sensor |
| USB ports | Front accessible |
| Power | Side USB-C |

### Dimensions

| Measurement | Value |
|-------------|-------|
| Outer | 100 x 70 x 35mm |
| Wall thickness | 2mm |
| Vent area | 30% of top surface |

### Features

- Front USB access (mic, radar via hub)
- Side GPIO slot for BCG wires
- Top ventilation with fan option
- Rubber feet for stability
- Optional LED window for status

---

## Mic Bracket

Clip or stand for USB microphone positioning.

### Options

1. **Nightstand clip**: Clamps to edge, gooseneck optional
2. **Weighted base**: Small stand with adjustable arm
3. **Wall clip**: Adhesive mount for wall positioning

### Design depends on mic chosen

MAONO AU-903: 16mm diameter body
Standard USB mic: ~25-30mm body

---

## Cable Management

### Cable Clips

- 6mm channel (USB cable)
- Adhesive back or screw mount
- Print in strips of 5-10

### Cable Raceway

- Optional longer channel for wall runs
- Snap-on cover
- Can paint to match wall

---

## Print Checklist

| Part | Qty | Material | Time | Priority |
|------|-----|----------|------|----------|
| Radar wall enclosure | 1 | PETG | 3h | High |
| Radar enclosure lid | 1 | PETG | 1h | High |
| Pi 5 case | 1 | PLA/PETG | 4h | Medium |
| Pi 5 case lid | 1 | PLA/PETG | 2h | Medium |
| Cable clips | 10 | PLA | 30m | Low |
| Mic bracket | 1 | PLA | 1h | Low |

**Total print time: ~12 hours**

---

## Files to Create

Once designs are finalized in CAD:

```
hardware/3d_prints/
├── radar_wall_enclosure.stl
├── radar_wall_enclosure_lid.stl
├── radar_ceiling_mount.stl
├── pi5_case_base.stl
├── pi5_case_lid.stl
├── mic_bracket_clip.stl
├── cable_clips_x10.stl
└── README.md
```

---

## Notes

- All dimensions include ~0.2mm tolerance for fit
- Test print a small section first to verify fit
- PETG preferred for enclosures (heat resistance, slight flex)
- PLA fine for clips and brackets
- Consider printing radar window area with 100% infill for rigidity
