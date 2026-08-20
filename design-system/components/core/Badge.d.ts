import * as React from "react";

/**
 * Small status / metadata label. `simulated` is reserved for mock sensor data — never
 * use violet for anything else.
 */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "neutral" | "accent" | "normal" | "warning" | "critical" | "simulated";
  /** Tracked-out 10px caps, used for SIM / MOCK / REQUIRED chips. */
  uppercase?: boolean;
}

export declare function Badge(props: BadgeProps): JSX.Element;
