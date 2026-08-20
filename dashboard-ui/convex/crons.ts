import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

/**
 * Scheduled retention.
 *
 * This file did not exist before. The cleanup mutations in vitals.ts were
 * written but never called by anything, so every table grew without bound.
 * The database reached 4.5 GB on the SD card, and the sustained write load
 * stalled the card's controller until all disk I/O on the device froze.
 *
 * Frequencies are chosen so each pass has little to do. Deletes are writes
 * too, so a steady trickle is far kinder to flash storage than an hourly
 * bulk purge - and it keeps the working set small enough that the database
 * size stays roughly constant instead of merely growing more slowly.
 */
const crons = cronJobs();

// The firehose: ~11 Hz in, 5 minute window out. Runs often because a minute
// of backlog is already ~660 rows.
crons.interval(
  "prune radar signal",
  { minutes: 1 },
  internal.vitals.pruneRadarSignal,
  {},
);

// Vitals history backing the charts: 48 hours.
crons.interval(
  "prune readings",
  { minutes: 10 },
  internal.vitals.pruneReadings,
  {},
);

// Resolved alerts older than 30 days. Unresolved alerts are never dropped.
crons.interval(
  "prune alerts",
  { hours: 6 },
  internal.vitals.pruneAlerts,
  {},
);

export default crons;
