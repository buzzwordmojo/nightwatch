import { mutation, query, internalMutation } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

// ============================================================================
// Retention policy
//
// Nothing bounded these tables before, so the database grew without limit
// until sustained writes stalled the SD card and froze the device. Retention
// is deliberately tight: the goal is a database whose size stays roughly
// CONSTANT, not one that merely grows slower.
//
// radarSignal is the firehose - inserted at ~11 Hz, which is ~950k rows/day.
// The schema always described it as a "5 minute rolling window"; the cleanup
// default of 12 hours contradicted that by a factor of 144.
// ============================================================================

export const RETENTION = {
  // Raw radar samples: visualisation only, never needed historically.
  radarSignalMinutes: 5,
  // Vitals history: what the charts read.
  readingsHours: 48,
  // Resolved alerts older than this are dropped; unresolved are always kept.
  alertsDays: 30,
} as const;

// Rows deleted per pass. Each delete is itself a write, so keep passes small
// and frequent rather than large and bursty - a struggling card copes far
// better with a steady trickle than with a spike.
const PRUNE_BATCH = 500;

// Bound on self-rescheduling passes, so a large backlog drains over several
// invocations instead of looping unbounded inside one.
const MAX_PASSES = 20;

// Update detector state (called by Python backend)
export const updateDetector = mutation({
  args: {
    detector: v.string(),
    state: v.string(),
    confidence: v.float64(),
    value: v.any(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("detectorState")
      .withIndex("by_detector", (q) => q.eq("detector", args.detector))
      .first();

    const data = {
      detector: args.detector,
      state: args.state,
      confidence: args.confidence,
      value: args.value,
      updatedAt: Date.now(),
    };

    if (existing) {
      await ctx.db.patch(existing._id, data);
      return existing._id;
    } else {
      return await ctx.db.insert("detectorState", data);
    }
  },
});

// Insert reading for historical chart
export const insertReading = mutation({
  args: {
    respirationRate: v.optional(v.float64()),
    heartRate: v.optional(v.float64()),
    breathingAmplitude: v.optional(v.float64()),
    signalQuality: v.optional(v.float64()),
    bedOccupied: v.optional(v.boolean()),
    fusionAgreement: v.optional(v.float64()),
    fusionSources: v.optional(v.float64()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("readings", {
      timestamp: Date.now(),
      ...args,
    });
  },
});

// Get all current detector states (real-time subscription)
export const getAllDetectors = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("detectorState").collect();
  },
});

// Get recent readings for chart
export const getRecentReadings = query({
  args: {
    minutes: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const minutes = Math.min(args.minutes ?? 30, 480); // Cap at 8 hours
    const cutoff = Date.now() - minutes * 60 * 1000;

    // For longer ranges, use server-side downsampling to avoid timeouts
    // By taking fewer records with larger gaps
    const maxRecords = minutes > 60 ? 500 : 1000;

    // Query newest first so the take() limit keeps recent data, not oldest
    const readings = await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.gte("timestamp", cutoff))
      .order("desc")
      .take(maxRecords);
    return readings.reverse();
  },
});

// Get combined current vitals
export const getCurrentVitals = query({
  args: {},
  handler: async (ctx) => {
    const detectors = await ctx.db.query("detectorState").collect();

    // Which detectors are simulated. Mock data may drive the per-detector
    // cards (with their SIM badges) but must never supply the headline
    // vitals: the mock BCG reports a permanently occupied bed with a
    // wiggling heart rate, and letting it fall through showed
    // "Occupied, 71 BPM" over a room the radar knew was empty.
    const statuses = await ctx.db.query("systemStatus").collect();
    const mocks = new Set(
      statuses.filter((c) => c.mock).map((c) => c.component),
    );

    // A detectorState doc is a snapshot, not a stream: when its writer goes
    // quiet the doc just sits there. Values older than this are treated as
    // absent rather than current.
    const STALE_MS = 15000;
    const now = Date.now();
    const fresh = (d: { updatedAt?: number }) =>
      d.updatedAt != null && now - d.updatedAt < STALE_MS;

    const vitals: Record<string, any> = {
      timestamp: Date.now(),
      respirationRate: null,
      heartRate: null,
      breathingDetected: null,
      bedOccupied: null,
      overallState: "normal",
      detectors: {},
    };

    let worstState = "normal";
    const stateOrder = ["normal", "uncertain", "warning", "alert"];

    for (const detector of detectors) {
      vitals.detectors[detector.detector] = {
        state: detector.state,
        confidence: detector.confidence,
        value: detector.value,
        updatedAt: detector.updatedAt,
      };

      const usable = fresh(detector) && !mocks.has(detector.detector);

      // Extract specific values from raw detectors (as fallbacks)
      if (usable && detector.detector === "radar") {
        vitals.respirationRate = detector.value?.respiration_rate ?? null;
        if (detector.value?.heart_rate != null) {
          vitals.heartRate = detector.value.heart_rate;
        }
        if (detector.value?.presence != null) {
          vitals.bedOccupied = detector.value.presence;
        }
      }
      if (usable && detector.detector === "audio") {
        vitals.breathingDetected = detector.value?.breathing_detected ?? null;
        if (!vitals.respirationRate && detector.value?.breathing_rate) {
          vitals.respirationRate = detector.value.breathing_rate;
        }
      }
      if (usable && detector.detector === "bcg") {
        vitals.heartRate = detector.value?.heart_rate ?? null;
        vitals.bedOccupied = detector.value?.bed_occupied ?? null;
      }

      // Fusion channels override raw values - but only while their writer is
      // alive. Fusion docs go stale exactly when their sources stop
      // contributing, which is exactly when they must not win.
      if (fresh(detector) && detector.detector === "fusion.respiration_rate") {
        if (detector.value?.value != null) {
          vitals.respirationRate = detector.value.value;
          vitals.fusionAgreement = detector.value.agreement ?? 1.0;
          vitals.fusionSources = detector.value.source_count ?? 1;
        }
      }
      if (fresh(detector) && detector.detector === "fusion.heart_rate") {
        if (detector.value?.value != null) {
          vitals.heartRate = detector.value.value;
        }
      }
      if (fresh(detector) && detector.detector === "fusion.presence") {
        if (detector.value?.value != null) {
          vitals.bedOccupied = detector.value.value;
        }
      }

      // Track worst state (skip fusion meta-detectors for state)
      if (!detector.detector.startsWith("fusion.")) {
        if (stateOrder.indexOf(detector.state) > stateOrder.indexOf(worstState)) {
          worstState = detector.state;
        }
      }
    }

    vitals.overallState = worstState;
    return vitals;
  },
});

// Cleanup old readings (keep last 24 hours)
export const cleanupReadings = mutation({
  args: {},
  handler: async (ctx) => {
    const cutoff = Date.now() - 24 * 60 * 60 * 1000;

    const oldReadings = await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.lt("timestamp", cutoff))
      .take(500); // Delete in batches

    let deleted = 0;
    for (const reading of oldReadings) {
      await ctx.db.delete(reading._id);
      deleted++;
    }

    return { deleted };
  },
});

// Aggressive cleanup - keep only last N minutes
export const purgeOldReadings = mutation({
  args: {
    keepMinutes: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const keepMinutes = args.keepMinutes ?? 30;
    const cutoff = Date.now() - keepMinutes * 60 * 1000;

    const oldReadings = await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.lt("timestamp", cutoff))
      .take(500); // Delete in batches to avoid timeout

    let deleted = 0;
    for (const reading of oldReadings) {
      await ctx.db.delete(reading._id);
      deleted++;
    }

    return { deleted, more: oldReadings.length === 500 };
  },
});

// ============================================================================
// Radar Signal Data (for visualization)
// ============================================================================

// Insert radar signal sample (called at ~11 Hz by Python backend)
export const insertRadarSignal = mutation({
  args: {
    x: v.number(),
    y: v.number(),
    distance: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("radarSignal", {
      timestamp: Date.now(),
      x: args.x,
      y: args.y,
      distance: args.distance,
    });
  },
});

// Get recent radar signal data for charts
export const getRadarSignal = query({
  args: {
    seconds: v.optional(v.number()),
    maxPoints: v.optional(v.number()), // Downsample to this many points max
  },
  handler: async (ctx, args) => {
    const seconds = args.seconds ?? 30;
    const maxPoints = args.maxPoints ?? 500; // Default to 500 points for rendering
    const cutoff = Date.now() - seconds * 1000;

    const allData = await ctx.db
      .query("radarSignal")
      .withIndex("by_timestamp", (q) => q.gte("timestamp", cutoff))
      .order("asc")
      .collect();

    // If we have more points than maxPoints, downsample
    if (allData.length <= maxPoints) {
      return allData;
    }

    // Simple downsampling: take every Nth point
    const step = Math.ceil(allData.length / maxPoints);
    const downsampled = [];
    for (let i = 0; i < allData.length; i += step) {
      downsampled.push(allData[i]);
    }
    return downsampled;
  },
});

// Cleanup old radar signal data (configurable, default 12 hours)
export const cleanupRadarSignal = mutation({
  args: {
    keepHours: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const keepHours = args.keepHours ?? 12;
    const cutoff = Date.now() - keepHours * 60 * 60 * 1000;

    const oldSignals = await ctx.db
      .query("radarSignal")
      .withIndex("by_timestamp", (q) => q.lt("timestamp", cutoff))
      .take(500); // Delete in batches

    let deleted = 0;
    for (const signal of oldSignals) {
      await ctx.db.delete(signal._id);
      deleted++;
    }

    return { deleted, more: oldSignals.length === 500 };
  },
});

// ============================================================================
// Scheduled retention (called by convex/crons.ts)
//
// The public mutations above delete at most one batch per call, which is
// fine for the manual "clean up now" button but cannot keep up on its own:
// radarSignal arrives at ~11 Hz (~660 rows/minute), so a once-a-minute
// 500-row pass falls permanently behind. These internal versions reschedule
// themselves until the backlog is drained.
// ============================================================================

export const pruneRadarSignal = internalMutation({
  args: { pass: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const pass = args.pass ?? 1;
    const cutoff = Date.now() - RETENTION.radarSignalMinutes * 60 * 1000;

    const old = await ctx.db
      .query("radarSignal")
      .withIndex("by_timestamp", (q) => q.lt("timestamp", cutoff))
      .take(PRUNE_BATCH);

    for (const row of old) {
      await ctx.db.delete(row._id);
    }

    const more = old.length === PRUNE_BATCH;
    if (more && pass < MAX_PASSES) {
      await ctx.scheduler.runAfter(0, internal.vitals.pruneRadarSignal, {
        pass: pass + 1,
      });
    }
    return { deleted: old.length, pass, more };
  },
});

export const pruneReadings = internalMutation({
  args: { pass: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const pass = args.pass ?? 1;
    const cutoff = Date.now() - RETENTION.readingsHours * 60 * 60 * 1000;

    const old = await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.lt("timestamp", cutoff))
      .take(PRUNE_BATCH);

    for (const row of old) {
      await ctx.db.delete(row._id);
    }

    const more = old.length === PRUNE_BATCH;
    if (more && pass < MAX_PASSES) {
      await ctx.scheduler.runAfter(0, internal.vitals.pruneReadings, {
        pass: pass + 1,
      });
    }
    return { deleted: old.length, pass, more };
  },
});

export const pruneAlerts = internalMutation({
  args: { pass: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const pass = args.pass ?? 1;
    const cutoff = Date.now() - RETENTION.alertsDays * 24 * 60 * 60 * 1000;

    const old = await ctx.db
      .query("alerts")
      .withIndex("by_triggered", (q) => q.lt("triggeredAt", cutoff))
      .take(PRUNE_BATCH);

    // An unresolved alert is never discarded, however old it is.
    const stale = old.filter((a) => a.resolved);
    for (const row of stale) {
      await ctx.db.delete(row._id);
    }

    const more = old.length === PRUNE_BATCH;
    if (more && pass < MAX_PASSES) {
      await ctx.scheduler.runAfter(0, internal.vitals.pruneAlerts, {
        pass: pass + 1,
      });
    }
    return { deleted: stale.length, scanned: old.length, pass, more };
  },
});
