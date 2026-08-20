import * as React from "react";

export interface SensorStatusEntry {
  key: string;
  label: string;
  /** lucide icon node at 12×12 — Radio, Mic, Activity. */
  icon?: React.ReactNode;
  connected?: boolean;
  status?: "running" | "online" | "normal" | "warning" | "degraded" | "uncertain" | "error" | "critical" | "alert" | string;
  signal?: number;
  /** Renders the violet SIM chip. */
  mock?: boolean;
}

/** Compact per-sensor status row that lives in the dashboard header. */
export interface SensorStatusBarProps {
  sensors: SensorStatusEntry[];
}

export declare function SensorStatusBar(props: SensorStatusBarProps): JSX.Element;
