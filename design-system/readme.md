# KnightWatcher Design System

KnightWatcher is the rebrand of **Nightwatch**, an open-source, non-contact epilepsy monitoring system for Raspberry Pi. It watches a sleeping child for signs of seizure activity using radar, audio, and bed-vibration (BCG) sensors — nothing is worn, nothing is attached, and no data leaves the house. A Python backend fuses the sensor signals, an alert engine raises warnings and criticals, and a Next.js dashboard shows the state of the room in real time.

It was built by a parent, for their kid, and released under MIT so other families can build one.

## Sources

- **Attached codebase:** `nightwatch/` (mounted local folder, read-only). Python package `nightwatch/`, dashboard `dashboard-ui/` (Next.js 15 + Tailwind + shadcn/ui + Convex), docs in `docs/` and `hardware/`.
- **Repo referenced in the source README:** `https://github.com/yourrepo/nightwatch.git` (placeholder in the original README — no live repo was accessible).
- No Figma file, slide deck, or brand guideline document was provided.
- No logo, icon, font, or image asset existed anywhere in the source repo (`dashboard-ui/public/` contains only `.gitkeep`).

## Rebrand

The user is exploring a rebrand from *Nightwatch* to **KnightWatcher**, with a new logo/wordmark as the priority. Direction confirmed by the user:

- Wordmark set camel-case and two-tone: **Knight** in foreground white, **Watcher** in brand blue.
- Mark: a shield containing a crescent moon — the knight/guard reading plus the night-watch reading, in one form.
- Palette: deep navy-black base, with bright purple `#5B21B6`/`#7C3AED` and yellow `#FACC15` replacing the dashboard's original blue accent.
- Type: geometric sans throughout (Space Grotesk).
- Tone: warm, human, family-made.

Everything else in this system is measured from the real codebase, not invented.

## Products

1. **Device dashboard** (`ui_kits/dashboard/`) — the always-dark monitoring view, the six-step setup wizard, the settings area, and the Wi-Fi captive portal the device serves from its own hotspot.
2. **Project landing page** (`ui_kits/marketing/`) — new surface for the rebrand; content lifted verbatim from the repo README and docs.

---

## Content fundamentals

The source copy is plain, second-person, and unembellished. It explains what a thing does and what it costs you, then stops.

- **Person:** "you" and "your" for the parent; "we" only in the setup wizard's first person plural ("Let's set up your monitoring system"). The child is named, never "the patient" or "the subject" — the wizard literally asks for a name and uses it.
- **Casing:** sentence case for everything — buttons ("Get Started", "Looks Good", "Play test"), headings ("Position your sensors"), settings labels ("Last Update", "Detector Status"). Uppercase is reserved for 10px micro-labels (`SIM`, `MOCK`, `WIFI NETWORK NAME`) and alert-level chips.
- **Length:** headings are 2–5 words. Descriptions are one sentence, no period-less fragments stacked together. Empty states are a single line: "No alerts in the last 24 hours".
- **Vocabulary:** the product's own words, used consistently — detector, sensor, vital, reading, alert, event, fusion, confidence, mock/simulated, acknowledge, resolve, pause. Sensor names stay technical where they're technical ("BCG Sensor", "HLK-LD2450").
- **Reassurance over drama.** Status copy states the fact: "All data stays on your device — no cloud required", "Monitoring paused for 15 more minutes". Alerts state the reading, not a diagnosis: "Respiration below 8 BPM", never "Seizure detected".
- **Honesty about maturity.** The repo says "Testing soon", "Planned", "in progress" — keep those. Never dress an unbuilt sensor as shipped.
- **Safety notice is non-negotiable and near-verbatim:** "This is not a medical device. It should supplement, not replace, proper medical supervision."
- **Emoji:** the source README opens with a 🌙 and uses ⚠️ for the safety notice. In product UI, **no emoji** — status is carried by colour, dots, and lucide icons. Keep it that way after the rebrand; the crescent lives in the mark now.
- **Vibe:** a capable parent explaining their build to another parent at 1am. Warm, specific, slightly technical, never markety. No exclamation marks except the one in "Contributions welcome!".

## Visual foundations

**Always dark.** The app sets `class="dark"` on `<html>` and has no light mode. The night scale runs `#020817` (app) → `#030B1C` (card) → `#0B1424` (raised) → `#1E293B` (border/muted) → `#94A3B8` (muted text) → `#F8FAFC` (text).

**Colour.** One accent: brand purple `#7C3AED` (hover `#8B5CF6`, focus ring and mark `#5B21B6`). Yellow `#FACC15` is the crescent in the mark and the warning state — it appears nowhere else. Three status colours: green `#16A34A` normal, amber/yellow `#FACC15` warning, red `#EF4444` critical. Cyan `#22D3EE` means *simulated data* and nothing else — never decorate with it (it replaced violet `#A855F7`, which now collides with the brand purple). Grey `#94A3B8` is offline/unknown. The dashboard's original blue accent (`#3B82F6`) is retired.

**The tinted-surface rule.** Every status surface is a 10% fill plus a 50%-alpha border of the same hue (`--fill-warning` + `--border-warning`). Icon chips inside them use a 20% fill. This is the single most recognisable pattern in the UI.

**Type.** Space Grotesk everywhere: 48/36px bold display with -2% tracking, 24/600 card titles, 16/400 body, 14 and 12 muted secondary, 10/700 uppercase at +12% tracking for micro-labels. JetBrains Mono for readings, percentages, SSIDs, commit hashes, and config snippets. Vitals are `tabular-nums` so a changing number doesn't shift the layout.

**Spacing.** 4px base. Page padding 16px mobile / 32px desktop, card padding 24px (16px for dense rows), grid gaps 16px, section gaps 32px. Settings content is capped at 1024px; the dashboard runs full width.

**Corners.** 8px cards and inputs, 6px buttons and menu rows, 4px small chips, pills for dots, meters, and level chips.

**Borders do the structural work; shadows barely exist.** Cards are a 1px `#1E293B` border with a near-invisible `shadow-sm`. Real shadow appears in exactly two places: dropdown menus and critical cards (a red-tinted lift).

**Backgrounds.** Flat colour only — no gradients, no photography, no illustration, no texture, no pattern. The one blur in the system is the landing page's sticky nav (`rgba(2,8,23,.8)` + `backdrop-filter: blur(8px)`). Transparency is used for status tints and disabled states (opacity .5), not for decoration.

**Motion is diagnostic, never decorative.** Four loops, all `cubic-bezier(.4,0,.2,1)`: `pulse-ring` 2s on healthy dots, `pulse-slow` 2s on warning cards and unacknowledged banners, `pulse-fast` 0.75s on critical cards, `breathe`/`breathing-glow` 4s for the all-clear state. Transitions are 150ms on colour, 200ms on layout, 300ms on card state. If nothing is wrong, nothing moves except the slow breathing pulse.

**States.** Hover = a fill step, not a transform: solid buttons darken ~10%, outline and ghost buttons take the muted surface, nav rows take `--surface-muted`, network rows take a blue border. Nothing scales or lifts on press. Focus = 2px blue ring at 50% alpha. Disabled = opacity .5 plus `cursor: not-allowed`.

**Imagery.** There is none, anywhere in the source — no photos, no illustrations, no stock. Data visualisation (line charts, level meters, radar aiming view) is the only picture the product draws. Don't add photography to this brand without asking; if a surface feels empty, a live reading belongs there instead.

## Iconography

- **lucide** is the icon set, used via `lucide-react` in the app. This system loads the same glyphs from the lucide UMD CDN (`https://unpkg.com/lucide@0.460.0/dist/umd/lucide.js`) and wraps them in `ui_kits/dashboard/icon.jsx`. Same library, same 2px stroke, same 24px grid — not a substitution.
- Sizes in use: 12px (sensor bar), 16px (buttons, rows, inputs), 20px (vital cards, feature circles), 24px (alert banners), 32px (empty states).
- Glyphs the product actually uses: `Moon`, `Heart`, `Wind`, `Activity`, `Radio`, `Mic`, `Settings`, `Volume2`, `VolumeX`, `Bell`, `Users`, `AlertTriangle`, `XCircle`, `Check`, `X`, `Pause`, `Play`, `Wifi`, `WifiOff`, `Lock`, `Eye`, `EyeOff`, `ArrowLeft`, `Clock`, `HardDrive`, `RotateCw`, `Download`, `Search`, `Smartphone`.
- Icons in circles: 40px circle, `--fill-accent` (purple at 12%) background, accent-coloured glyph (features); status-tinted 20% background for vital-card chips.
- The old `Moon` glyph did double duty as the Nightwatch logo in the header. After the rebrand the header carries the KnightWatcher mark instead, and `Moon` goes back to meaning "bed/sleep".
- **No emoji in UI. No hand-drawn SVG.** A few source components inline raw Heroicons-style `<path>`s (the welcome step); those are lucide equivalents here (`CircleCheck`, `Bell`, `Lock`).

## Components

Built from the inventory the codebase defines (`src/components/ui`, `dashboard`, `setup`, `wifi`).

**`components/core/`** — `Button`, `Card` (with `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`), `Badge`, `StatusIndicator`, `Progress`, `Slider`
**`components/monitoring/`** — `VitalCard`, `AlertBanner`, `SensorStatusBar`, `AudioLevelMeter`, `EventRow`, `PauseButton`
**`components/onboarding/`** — `StepProgress`, `FeatureItem`, `SensorItem`, `NetworkRow`, `TextField`
**`components/brand/`** — `Logo`

**Intentional additions**
- `Badge` — the codebase repeats an inline chip (`px-2 py-1 rounded text-xs`) in five places; promoted to one component.
- `TextField` — the source only has `PasswordInput`; generalised so the wizard's name field uses the same input.
- `EventRow` — extracted from `EventsList`, which owned both consolidation logic and row markup. The consolidation logic stays in the app.
- `Logo` — the rebrand's whole point; no equivalent existed.

**Deliberately not built:** `DropdownMenu` and `Tooltip` (Radix primitives with no KnightWatcher-specific styling), `RadarAimingView`, `RadarSignalChart`, `VitalsChart` (product-specific canvas/recharts views — the dashboard kit draws a simple stand-in), and the certificate install/trust cards.

## Index

```
styles.css              @import list — the only file consumers link
tokens/                 fonts, colors, typography, spacing, elevation, motion
assets/                 logo.svg, mark.svg, wordmark.svg
components/             core/, monitoring/, onboarding/, brand/ — each with .jsx, .d.ts, .prompt.md, and a card
guidelines/             foundation specimen cards (Colors, Type, Spacing, Brand)
ui_kits/dashboard/      index.html click-through + DashboardScreen, SetupScreen, SettingsScreen, PortalScreen
ui_kits/marketing/      index.html + LandingPage
thumbnail.html          homepage tile
SKILL.md                Agent Skills entry point
```

## Caveats

- **Fonts are a substitution.** The source ships no webfonts (system stack only). Space Grotesk and JetBrains Mono load from Google Fonts. If the rebrand buys a licensed face, drop the files in `assets/fonts/` and rewrite `tokens/fonts.css`.
- **The logo is new work, not a recovered asset.** No mark existed in the sources; the shield-and-crescent was drawn for this rebrand and is a starting point for a real designer, not a finished identity.
