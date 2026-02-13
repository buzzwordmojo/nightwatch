import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Current state from each detector (latest reading)
  detectorState: defineTable({
    detector: v.string(), // "radar" | "audio" | "bcg"
    state: v.string(), // "normal" | "warning" | "alert" | "uncertain"
    confidence: v.float64(),
    value: v.any(), // Detector-specific values
    updatedAt: v.number(), // Unix timestamp ms
  }).index("by_detector", ["detector"]),

  // Historical readings for charts
  readings: defineTable({
    timestamp: v.number(), // Unix timestamp ms
    respirationRate: v.optional(v.float64()),
    heartRate: v.optional(v.float64()),
    breathingAmplitude: v.optional(v.float64()),
    signalQuality: v.optional(v.float64()),
    bedOccupied: v.optional(v.boolean()),
  }).index("by_timestamp", ["timestamp"]),

  // Alert history
  alerts: defineTable({
    alertId: v.string(),
    level: v.string(), // "warning" | "critical"
    source: v.string(), // detector name
    message: v.string(),
    triggeredAt: v.number(),
    acknowledgedAt: v.optional(v.number()),
    acknowledgedBy: v.optional(v.string()),
    resolved: v.boolean(),
    resolvedAt: v.optional(v.number()),
  })
    .index("by_triggered", ["triggeredAt"])
    .index("by_resolved", ["resolved"]),

  // System status
  systemStatus: defineTable({
    component: v.string(), // "radar" | "audio" | "bcg" | "engine" | "notifier"
    status: v.string(), // "online" | "offline" | "error"
    message: v.optional(v.string()),
    updatedAt: v.number(),
  }).index("by_component", ["component"]),

  // Settings
  settings: defineTable({
    key: v.string(),
    value: v.any(),
  }).index("by_key", ["key"]),
});
