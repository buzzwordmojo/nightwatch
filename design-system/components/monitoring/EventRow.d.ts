import * as React from "react";

/**
 * One consolidated event period in the 24-hour history list. Consecutive alerts from the
 * same detector within 30s are merged upstream and reported here with a `count`.
 */
export interface EventRowProps {
  /** Detector key; mapped to a human label (radar → "Breathing", bcg → "Heart Rate"). */
  source: string;
  level?: "warning" | "critical" | "alert" | string;
  message: string;
  /** Preformatted times, e.g. "2:14 AM". */
  startTime: string;
  endTime?: string;
  /** Preformatted span, e.g. "1m 20s". */
  duration?: string;
  ongoing?: boolean;
  count?: number;
  icon?: React.ReactNode;
}

export declare function EventRow(props: EventRowProps): JSX.Element;
