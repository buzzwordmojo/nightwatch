/* eslint-disable */
/**
 * Generated API types for Convex.
 *
 * THIS FILE IS GENERATED - DO NOT EDIT
 */

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

import type * as alerts from "../alerts.js";
import type * as system from "../system.js";
import type * as vitals from "../vitals.js";

/**
 * A utility for referencing Convex functions in your app's API.
 */
declare const fullApi: ApiFromModules<{
  alerts: typeof alerts;
  system: typeof system;
  vitals: typeof vitals;
}>;

export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;
