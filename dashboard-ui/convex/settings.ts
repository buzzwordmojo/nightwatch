import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Get a setting by key
export const get = query({
  args: { key: v.string() },
  handler: async (ctx, args) => {
    const setting = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();
    return setting?.value ?? null;
  },
});

// Get all settings
export const getAll = query({
  args: {},
  handler: async (ctx) => {
    const settings = await ctx.db.query("settings").collect();
    const result: Record<string, unknown> = {};
    for (const s of settings) {
      result[s.key] = s.value;
    }
    return result;
  },
});

// Set a setting
export const set = mutation({
  args: {
    key: v.string(),
    value: v.any(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, { value: args.value });
      return existing._id;
    } else {
      return await ctx.db.insert("settings", {
        key: args.key,
        value: args.value,
      });
    }
  },
});

// Delete a setting
export const remove = mutation({
  args: { key: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", args.key))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
      return true;
    }
    return false;
  },
});

// Bulk set multiple settings
export const setMany = mutation({
  args: {
    settings: v.array(
      v.object({
        key: v.string(),
        value: v.any(),
      })
    ),
  },
  handler: async (ctx, args) => {
    for (const { key, value } of args.settings) {
      const existing = await ctx.db
        .query("settings")
        .withIndex("by_key", (q) => q.eq("key", key))
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, { value });
      } else {
        await ctx.db.insert("settings", { key, value });
      }
    }
    return true;
  },
});

// Audio settings defaults
const AUDIO_DEFAULTS = {
  gain: 50.0,
  breathing_threshold: 0.005,
  silence_threshold: 0.001,
  breathing_freq_min_hz: 100.0,
  breathing_freq_max_hz: 1200.0,
};

// Get audio settings with defaults
export const getAudioSettings = query({
  args: {},
  handler: async (ctx) => {
    const settings = await ctx.db.query("settings").collect();
    const result = { ...AUDIO_DEFAULTS };

    for (const s of settings) {
      if (s.key.startsWith("audio.")) {
        const key = s.key.replace("audio.", "") as keyof typeof AUDIO_DEFAULTS;
        if (key in AUDIO_DEFAULTS) {
          result[key] = s.value as number;
        }
      }
    }

    return result;
  },
});

// Update audio settings and flag for apply
export const setAudioSettings = mutation({
  args: {
    gain: v.optional(v.number()),
    breathing_threshold: v.optional(v.number()),
    silence_threshold: v.optional(v.number()),
    breathing_freq_min_hz: v.optional(v.number()),
    breathing_freq_max_hz: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const updates: { key: string; value: number }[] = [];

    if (args.gain !== undefined) {
      updates.push({ key: "audio.gain", value: args.gain });
    }
    if (args.breathing_threshold !== undefined) {
      updates.push({ key: "audio.breathing_threshold", value: args.breathing_threshold });
    }
    if (args.silence_threshold !== undefined) {
      updates.push({ key: "audio.silence_threshold", value: args.silence_threshold });
    }
    if (args.breathing_freq_min_hz !== undefined) {
      updates.push({ key: "audio.breathing_freq_min_hz", value: args.breathing_freq_min_hz });
    }
    if (args.breathing_freq_max_hz !== undefined) {
      updates.push({ key: "audio.breathing_freq_max_hz", value: args.breathing_freq_max_hz });
    }

    for (const { key, value } of updates) {
      const existing = await ctx.db
        .query("settings")
        .withIndex("by_key", (q) => q.eq("key", key))
        .first();

      if (existing) {
        await ctx.db.patch(existing._id, { value });
      } else {
        await ctx.db.insert("settings", { key, value });
      }
    }

    // Set flag to indicate settings need to be applied to backend
    const pendingKey = "audio.pending_apply";
    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", pendingKey))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, { value: Date.now() });
    } else {
      await ctx.db.insert("settings", { key: pendingKey, value: Date.now() });
    }

    return true;
  },
});

// Clear pending apply flag (called after backend applies settings)
export const clearAudioPending = mutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db
      .query("settings")
      .withIndex("by_key", (q) => q.eq("key", "audio.pending_apply"))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
    }
    return true;
  },
});
