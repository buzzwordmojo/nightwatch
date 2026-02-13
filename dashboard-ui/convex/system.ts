import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Update component status
export const updateStatus = mutation({
  args: {
    component: v.string(),
    status: v.string(),
    message: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("systemStatus")
      .withIndex("by_component", (q) => q.eq("component", args.component))
      .first();

    const data = {
      component: args.component,
      status: args.status,
      message: args.message,
      updatedAt: Date.now(),
    };

    if (existing) {
      await ctx.db.patch(existing._id, data);
      return existing._id;
    } else {
      return await ctx.db.insert("systemStatus", data);
    }
  },
});

// Get all component statuses
export const getAll = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("systemStatus").collect();
  },
});

// Get system health overview
export const getHealth = query({
  args: {},
  handler: async (ctx) => {
    const components = await ctx.db.query("systemStatus").collect();

    let overall = "online";
    let lastUpdate = 0;
    const componentMap: Record<string, { status: string; message?: string }> = {};

    for (const comp of components) {
      componentMap[comp.component] = {
        status: comp.status,
        message: comp.message,
      };

      if (comp.updatedAt > lastUpdate) {
        lastUpdate = comp.updatedAt;
      }

      if (comp.status === "error") {
        overall = "degraded";
      }
      if (comp.status === "offline") {
        overall = "error";
      }
    }

    // Check for stale data
    if (Date.now() - lastUpdate > 30000 && lastUpdate > 0) {
      overall = "stale";
    }

    return {
      overall,
      components: componentMap,
      lastUpdate,
    };
  },
});

// Pause monitoring
export const pause = mutation({
  args: {
    durationMinutes: v.number(),
  },
  handler: async (ctx, args) => {
    const pauseUntil = Date.now() + args.durationMinutes * 60 * 1000;

    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", "pauseUntil"))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, { value: pauseUntil });
    } else {
      await ctx.db.insert("settings", { key: "pauseUntil", value: pauseUntil });
    }

    return pauseUntil;
  },
});

// Resume monitoring
export const resume = mutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", "pauseUntil"))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
    }
    return true;
  },
});

// Check if paused
export const isPaused = query({
  args: {},
  handler: async (ctx) => {
    const setting = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", "pauseUntil"))
      .first();

    if (!setting) return { paused: false };

    const pauseUntil = setting.value as number;
    const now = Date.now();

    if (pauseUntil > now) {
      return {
        paused: true,
        pauseUntil,
        remainingMinutes: Math.ceil((pauseUntil - now) / 60000),
      };
    }

    return { paused: false };
  },
});
