import * as React from "react";

/** Detected/not-detected sensor row in the setup wizard's positioning step. */
export interface SensorItemProps {
  name: string;
  description: string;
  detected?: boolean;
  /** 0–100; only shown when detected. */
  signal?: number;
  required?: boolean;
  optional?: boolean;
  /** lucide node at 20×20 — Check when detected, X when not. */
  icon?: React.ReactNode;
}

export declare function SensorItem(props: SensorItemProps): JSX.Element;
