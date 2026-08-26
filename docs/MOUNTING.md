# Mounting a 60GHz vitals radar

**Read this before buying or installing.** With an LD6002-class sensor, aim is
not a finishing touch — it decides whether the system works at all. Measured on
identical hardware, same room, same person, varying only how the sensor was
pointed:

| Setup | Lock quality |
|---|---|
| Sitting incidentally near a desk-propped sensor | **26%** |
| Hand-aimed at the sternum, ~0.5–1 m | **79%** |
| Deliberately mounted and aimed over a bed | **100%** |

"Lock" means the module is actually measuring a chest. Without it you get no
respiration and no heart rate — the sensor reports a person is present but
tells you nothing about them.

## What the module is doing

A 60GHz FMCW radar measures **sub-millimetre chest displacement**. That is a
tiny signal, and everything below follows from protecting it.

The module has two output modes, and they are near-inversions of each other:

| | Locked (measuring) | Not locked |
|---|---|---|
| Phase frames | ~50 Hz | none |
| Rate frames | sparse, real values | ~50 Hz of `0.0` placeholders |

An empty room and a still person the sensor cannot lock onto look **almost
identical** on the wire. The difference is that a truly empty room stops
sending target frames entirely.

## Rules, in order of impact

### 1. Point at the chest, not at the body

Chest motion is toward and away from the sensor — that is the axis the radar
measures. A sensor above the head looking down the length of a body sees very
little of it. Aim square at the torso: beside the bed at chest height, or above
angled onto the chest.

### 2. Respect the range window

The LD6002 specifies **0.4–1.5 m** for respiration and heart rate. Note there is
a *minimum* as well as a maximum — mounting it inches from the sleeper is its
own failure mode. Aim for the middle of the band.

Presence detection reaches considerably further than vitals measurement, so a
seller's headline range figure is usually the *presence* number. The vitals
number is the one that matters here.

### 3. Mount rigidly

A propped or flexing sensor drifts out of aim, and the failure looks like a
flaky sensor rather than a mechanical problem. Rigid mount, fixed angle. If you
want to experiment with angles, print or build several fixed wedges rather than
using an adjustable joint that can sag.

### 4. Stillness is the operating condition, not an edge case

This device watches someone sleep. A sleeping person is the stillest target
you will ever ask a radar to measure, and marginal geometry fails precisely
when the subject stops moving — the sensor may hold lock while they shift and
lose it once they settle. **Always validate on a motionless person**, never on
someone who happens to be fidgeting.

### 5. Keep metal and coatings out of the beam

Bedding, plastics and wood are effectively transparent at 60GHz. Metal, foil
and metallised coatings are not.

Glass deserves specific warning: ordinary glass costs a few dB per pass — paid
twice, out and back — and **low-emissivity coated glass**, common in modern
windows and picture frames and invisible to the eye, behaves like a mirror at
these frequencies. Do not put the sensor behind glass.

### 6. If you enclose it, print a thin radome

A printed front cover can be nearly free if you keep three things true:

- **~1.6 mm wall thickness** — roughly a half-wavelength in PLA/PETG, so front
  and back surface reflections cancel
- **100% infill across the window** — sparse infill is an unpredictable
  air/plastic foam that scatters
- **Plain filament only** — no silk, metallic or carbon-fibre blends

An open cutout in front of the antenna is the zero-risk alternative.

## Validating your installation

Do not trust theory, including this document. Measure:

1. Put the sensor in its final position with the subject lying **as they
   actually sleep**.
2. Have them stay still for five minutes.
3. Check what fraction of that time produced live respiration and heart rate.

**Acceptance:** vitals present essentially continuously, with a continuous
stretch of at least a minute. Short dropouts of a few seconds are tolerable —
presence and alerting ride through them — but they are measurement gaps, and
enough of them delays how quickly a respiratory alert can trigger.

If you are below that, change the geometry before changing anything else. Aim
is worth more than any amount of software.
