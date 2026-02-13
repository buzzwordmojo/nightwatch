import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Create a new alert
export const create = mutation({
  args: {
    alertId: v.string(),
    level: v.string(),
    source: v.string(),
    message: v.string(),
  },
  handler: async (ctx, args) => {
    // Check if alert already exists
    const existing = await ctx.db
      .query("alerts")
      .filter((q) => q.eq(q.field("alertId"), args.alertId))
      .first();

    if (existing) {
      return existing._id;
    }

    return await ctx.db.insert("alerts", {
      alertId: args.alertId,
      level: args.level,
      source: args.source,
      message: args.message,
      triggeredAt: Date.now(),
      resolved: false,
    });
  },
});

// Acknowledge an alert
export const acknowledge = mutation({
  args: {
    alertId: v.string(),
  },
  handler: async (ctx, args) => {
    const alert = await ctx.db
      .query("alerts")
      .filter((q) => q.eq(q.field("alertId"), args.alertId))
      .first();

    if (alert && !alert.acknowledgedAt) {
      await ctx.db.patch(alert._id, {
        acknowledgedAt: Date.now(),
        acknowledgedBy: "dashboard",
      });
      return true;
    }
    return false;
  },
});

// Resolve an alert
export const resolve = mutation({
  args: {
    alertId: v.string(),
  },
  handler: async (ctx, args) => {
    const alert = await ctx.db
      .query("alerts")
      .filter((q) => q.eq(q.field("alertId"), args.alertId))
      .first();

    if (alert && !alert.resolved) {
      await ctx.db.patch(alert._id, {
        resolved: true,
        resolvedAt: Date.now(),
      });
      return true;
    }
    return false;
  },
});

// Get active alerts (unresolved)
export const getActive = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("alerts")
      .withIndex("by_resolved", (q) => q.eq("resolved", false))
      .order("desc")
      .collect();
  },
});

// Get recent alerts
export const getRecent = query({
  args: {
    hours: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const hours = args.hours ?? 24;
    const cutoff = Date.now() - hours * 60 * 60 * 1000;

    return await ctx.db
      .query("alerts")
      .withIndex("by_triggered", (q) => q.gte("triggeredAt", cutoff))
      .order("desc")
      .collect();
  },
});
