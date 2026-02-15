import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Get all alert rules
export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("alertRules").collect();
  },
});

// Get a single alert rule by name
export const get = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("alertRules")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();
  },
});

// Create or update an alert rule
export const upsert = mutation({
  args: {
    name: v.string(),
    enabled: v.boolean(),
    detector: v.string(),
    field: v.string(),
    operator: v.string(),
    value: v.number(),
    durationSeconds: v.number(),
    severity: v.string(),
    message: v.string(),
    cooldownSeconds: v.number(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("alertRules")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, args);
      return existing._id;
    } else {
      return await ctx.db.insert("alertRules", args);
    }
  },
});

// Toggle a rule's enabled state
export const toggle = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const rule = await ctx.db
      .query("alertRules")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    if (rule) {
      await ctx.db.patch(rule._id, { enabled: !rule.enabled });
      return !rule.enabled;
    }
    return null;
  },
});

// Delete an alert rule
export const remove = mutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const rule = await ctx.db
      .query("alertRules")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    if (rule) {
      await ctx.db.delete(rule._id);
      return true;
    }
    return false;
  },
});

// Seed default rules from config
export const seedDefaults = mutation({
  args: {},
  handler: async (ctx) => {
    const defaults = [
      {
        name: "Respiration critical",
        enabled: true,
        detector: "radar",
        field: "value.respiration_rate",
        operator: "<",
        value: 4,
        durationSeconds: 10,
        severity: "critical",
        message: "Respiration rate critically low ({respiration_rate} BPM)",
        cooldownSeconds: 60,
      },
      {
        name: "Respiration low",
        enabled: true,
        detector: "radar",
        field: "value.respiration_rate",
        operator: "<",
        value: 8,
        durationSeconds: 15,
        severity: "warning",
        message: "Respiration rate low ({respiration_rate} BPM)",
        cooldownSeconds: 30,
      },
      {
        name: "Subject not detected",
        enabled: true,
        detector: "radar",
        field: "value.presence",
        operator: "==",
        value: 0,
        durationSeconds: 30,
        severity: "warning",
        message: "Subject not detected by radar",
        cooldownSeconds: 60,
      },
    ];

    for (const rule of defaults) {
      const existing = await ctx.db
        .query("alertRules")
        .withIndex("by_name", (q) => q.eq("name", rule.name))
        .first();

      if (!existing) {
        await ctx.db.insert("alertRules", rule);
      }
    }

    return true;
  },
});
