/**
 * Coloured dot for system / detector state. Healthy states pulse-ring so a still
 * dashboard still reads as "alive".
 */
export interface StatusIndicatorProps {
  status: "online" | "normal" | "warning" | "degraded" | "stale" | "error" | "alert" | "critical" | "offline" | string;
  /** Renders "Label: status" beside the dot. */
  label?: string;
  size?: "sm" | "md" | "lg";
}

export declare function StatusIndicator(props: StatusIndicatorProps): JSX.Element;
