import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Generate a random token
function generateToken(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let token = "";
  for (let i = 0; i < 32; i++) {
    token += chars[Math.floor(Math.random() * chars.length)];
  }
  return token;
}

// Create a new share link
export const create = mutation({
  args: {
    name: v.string(),
    permissions: v.optional(v.string()),
    expiresInDays: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const token = generateToken();
    const now = Date.now();

    const id = await ctx.db.insert("shareLinks", {
      token,
      name: args.name,
      createdAt: now,
      expiresAt: args.expiresInDays
        ? now + args.expiresInDays * 24 * 60 * 60 * 1000
        : undefined,
      permissions: args.permissions ?? "view",
      active: true,
    });

    return { id, token };
  },
});

// Get all share links
export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("shareLinks").collect();
  },
});

// Validate a share token
export const validate = query({
  args: { token: v.string() },
  handler: async (ctx, args) => {
    const link = await ctx.db
      .query("shareLinks")
      .withIndex("by_token", (q) => q.eq("token", args.token))
      .first();

    if (!link) {
      return { valid: false, reason: "not_found" };
    }

    if (!link.active) {
      return { valid: false, reason: "revoked" };
    }

    if (link.expiresAt && link.expiresAt < Date.now()) {
      return { valid: false, reason: "expired" };
    }

    return {
      valid: true,
      permissions: link.permissions,
      name: link.name,
    };
  },
});

// Revoke a share link
export const revoke = mutation({
  args: { token: v.string() },
  handler: async (ctx, args) => {
    const link = await ctx.db
      .query("shareLinks")
      .withIndex("by_token", (q) => q.eq("token", args.token))
      .first();

    if (link) {
      await ctx.db.patch(link._id, { active: false });
      return true;
    }
    return false;
  },
});

// Delete a share link
export const remove = mutation({
  args: { token: v.string() },
  handler: async (ctx, args) => {
    const link = await ctx.db
      .query("shareLinks")
      .withIndex("by_token", (q) => q.eq("token", args.token))
      .first();

    if (link) {
      await ctx.db.delete(link._id);
      return true;
    }
    return false;
  },
});
