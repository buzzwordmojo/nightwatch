import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

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

    return await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.gte("timestamp", cutoff))
      .order("asc")
      .take(maxRecords);
  },
});

// Get combined current vitals
export const getCurrentVitals = query({
  args: {},
  handler: async (ctx) => {
    const detectors = await ctx.db.query("detectorState").collect();

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

      // Extract specific values
      if (detector.detector === "radar") {
        vitals.respirationRate = detector.value?.respiration_rate ?? null;
      }
      if (detector.detector === "audio") {
        vitals.breathingDetected = detector.value?.breathing_detected ?? null;
        if (!vitals.respirationRate && detector.value?.breathing_rate) {
          vitals.respirationRate = detector.value.breathing_rate;
        }
      }
      if (detector.detector === "bcg") {
        vitals.heartRate = detector.value?.heart_rate ?? null;
        vitals.bedOccupied = detector.value?.bed_occupied ?? null;
      }

      // Track worst state
      if (stateOrder.indexOf(detector.state) > stateOrder.indexOf(worstState)) {
        worstState = detector.state;
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
