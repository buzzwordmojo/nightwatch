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

// NOTE: there is deliberately no seedDefaults here.
// The monitor seeds this table from its own config.yaml at startup
// (nightwatch/core/alert_rules.py). A second seeder in the dashboard would race
// it with a hardcoded copy of the thresholds that could drift from the real ones.
