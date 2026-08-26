# Over-the-air updates — design

Status: **design agreed 2026-08-25, not yet built.** Supersedes
`scripts/self-update.sh`, which builds on-device and has never successfully
run (see "Why the current one fails").

## The constraint that shapes everything

This device watches a child sleep. **An update is a monitoring gap.** Every
decision below follows from that: gaps must be deliberate, brief, and
recoverable, and a failed update must never leave a device that cannot watch.

A stale monitor is safe. A bricked monitor is not.

## Why the current one fails

Four independent blockers, each fatal, all discovered by audit rather than by
it ever running:

1. `git clone` into `/home/pi/nightwatch` fails — the directory is non-empty
   because `flash-sd` *copies* the tree rather than cloning it.
2. The service runs with `ProtectHome=true`, so `/home/pi/...` does not exist
   inside its mount namespace. `_update_apply` cannot even see the script.
3. No sudoers rule for the `nightwatch` user, so `sudo self-update.sh` waits
   forever on a password prompt.
4. Node 18 on the Pi; the Convex CLI needs 20+, so function/schema deploys are
   **silently skipped** while the update reports success.

Blockers 1-3 are accidents. Blocker 4 is a symptom of the real problem: the
device is being asked to be a build machine.

## Model: build elsewhere, ship an artifact

The Pi unpacks and swaps. It never runs `npm`, never needs a toolchain, and
never has a half-built tree.

```
dev machine / CI                    device
────────────────                    ──────
build python wheel        ──┐
build dashboard (next)      ├─→  nightwatch-<version>.tar.zst  (+ .sha256)
pre-generate convex bundle ─┘         │
                                      ▼
                            verify checksum
                            unpack beside current
                            atomic symlink swap
                            restart, health-check
                            rollback on failure
```

### Artifact contents

| Path | Built by | Notes |
|---|---|---|
| `wheel/nightwatch-*.whl` | `python -m build` | no compilation on device |
| `dashboard/` | `next build` standalone + static | already how we deploy manually |
| `convex/` | pre-generated bundle | until Node 20 exists on the Pi |
| `MANIFEST` | build script | version, git sha, build time, checksums |

### Layout on device

```
/opt/nightwatch/releases/2026-08-25T2130-663472d/   ← unpacked artifact
/opt/nightwatch/releases/2026-08-24T1900-cd68b06/   ← previous, kept
/opt/nightwatch/current -> releases/2026-08-25T...  ← atomic symlink
```

Keep **two** releases. Rollback is a symlink swap plus a restart, needs no
network, and works when the update server is exactly what is broken.

## Safety interlocks

These are the point of the exercise, not decoration.

1. **Refuse while occupied.** The sensor already knows if someone is in bed.
   An update while the monitored person sleeps is not a maintenance window;
   it is a blind spot. Require the bed empty, or an explicit `force` from a human who
   understands what they are doing.
2. **Health-check after restart, auto-rollback on failure.** "Service started"
   is not health — this project has already shipped a service that started
   fine and could not alert. Health means: process up, detectors connected,
   and an event emitted within N seconds. Anything less, revert.
3. **Checksum before unpacking.** A truncated download must fail loudly, not
   install partially.
4. **Never update on boot.** A device that updates when it starts can boot-loop
   itself out of service, and the failure arrives at 3 am.
5. **Report the outcome off-device.** The dead man's switch already reaches
   email and ntfy; an update result should use it. An update that silently
   failed is indistinguishable from one that never ran.

## Permissions

The service must not be able to update itself directly. Instead:

- a small root-owned `nightwatch-apply-update` helper, its **only** ability
  being: verify checksum, unpack, swap symlink, restart, health-check, roll
  back;
- one sudoers rule scoped to that exact binary for the `nightwatch` user;
- the artifact staged into `/var/lib/nightwatch/staging`, which the service can
  already write (it is in `ReadWritePaths`), sidestepping the `ProtectHome`
  problem entirely rather than poking a hole in the hardening.

## Delivery

Start with **pull**: the device polls a URL for a manifest, compares versions,
downloads if newer, and applies only when the interlocks allow. No inbound
ports, works behind any NAT, and the same mechanism serves one device or
several. The artifact can live in S3 (the AWS account is already in use for
the watchdog) or as a GitHub release asset — the repo is public, so no
credentials on the device.

Automatic application stays **off** by default. The device checks and reports;
a human decides. That can relax later, once rollback has proven itself.

## Build order

1. Build script producing a versioned, checksummed artifact
2. `nightwatch-apply-update` helper with unpack/swap/rollback
3. Health-check definition (reuse the dead man's switch's `monitoring_health`)
4. Release layout migration on the device
5. Pull-check + manifest, reporting through the existing alert channels
6. Occupancy interlock
7. Dashboard surfacing: current version, available version, apply button

Steps 1-4 are the useful core; 5-7 are convenience on top.

## Open questions

- Where do artifacts live: S3 or GitHub releases?
- Does `flash-sd` ship a release artifact instead of a source copy, so a fresh
  card and an updated device are the same shape?
- Convex schema migrations: what happens when a new schema meets an old
  database, and can that roll back?
