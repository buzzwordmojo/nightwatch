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
    const minutes = args.minutes ?? 30;
    const cutoff = Date.now() - minutes * 60 * 1000;

    return await ctx.db
      .query("readings")
      .withIndex("by_timestamp", (q) => q.gte("timestamp", cutoff))
      .order("asc")
      .collect();
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
      .collect();

    let deleted = 0;
    for (const reading of oldReadings) {
      await ctx.db.delete(reading._id);
      deleted++;
    }

    return { deleted };
  },
});
