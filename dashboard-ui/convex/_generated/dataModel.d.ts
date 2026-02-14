/* eslint-disable */
/**
 * Generated data model types for Convex.
 *
 * THIS FILE IS GENERATED - DO NOT EDIT
 */

import type { GenericDataModel, GenericDocument, GenericTableInfo } from "convex/server";
import type { GenericId } from "convex/values";

export type TableNames =
  | "detectorState"
  | "readings"
  | "alerts"
  | "systemStatus"
  | "settings";

export type DataModel = {
  detectorState: {
    document: {
      _id: GenericId<"detectorState">;
      _creationTime: number;
      detector: string;
      state: string;
      confidence: number;
      value: any;
      updatedAt: number;
    };
    fieldPaths: "_id" | "_creationTime" | "detector" | "state" | "confidence" | "value" | "updatedAt";
    indexes: {
      by_detector: ["detector", "_creationTime"];
    };
    searchIndexes: {};
    vectorIndexes: {};
  };
  readings: {
    document: {
      _id: GenericId<"readings">;
      _creationTime: number;
      timestamp: number;
      respirationRate?: number;
      heartRate?: number;
      breathingAmplitude?: number;
      signalQuality?: number;
      bedOccupied?: boolean;
    };
    fieldPaths: "_id" | "_creationTime" | "timestamp" | "respirationRate" | "heartRate" | "breathingAmplitude" | "signalQuality" | "bedOccupied";
    indexes: {
      by_timestamp: ["timestamp", "_creationTime"];
    };
    searchIndexes: {};
    vectorIndexes: {};
  };
  alerts: {
    document: {
      _id: GenericId<"alerts">;
      _creationTime: number;
      alertId: string;
      level: string;
      source: string;
      message: string;
      triggeredAt: number;
      acknowledgedAt?: number;
      acknowledgedBy?: string;
      resolved: boolean;
      resolvedAt?: number;
    };
    fieldPaths: "_id" | "_creationTime" | "alertId" | "level" | "source" | "message" | "triggeredAt" | "acknowledgedAt" | "acknowledgedBy" | "resolved" | "resolvedAt";
    indexes: {
      by_triggered: ["triggeredAt", "_creationTime"];
      by_resolved: ["resolved", "_creationTime"];
    };
    searchIndexes: {};
    vectorIndexes: {};
  };
  systemStatus: {
    document: {
      _id: GenericId<"systemStatus">;
      _creationTime: number;
      component: string;
      status: string;
      message?: string;
      updatedAt: number;
    };
    fieldPaths: "_id" | "_creationTime" | "component" | "status" | "message" | "updatedAt";
    indexes: {
      by_component: ["component", "_creationTime"];
    };
    searchIndexes: {};
    vectorIndexes: {};
  };
  settings: {
    document: {
      _id: GenericId<"settings">;
      _creationTime: number;
      key: string;
      value: any;
    };
    fieldPaths: "_id" | "_creationTime" | "key" | "value";
    indexes: {
      by_key: ["key", "_creationTime"];
    };
    searchIndexes: {};
    vectorIndexes: {};
  };
};
