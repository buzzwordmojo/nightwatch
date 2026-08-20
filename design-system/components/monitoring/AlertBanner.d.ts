import * as React from "react";

/**
 * Full-width active alert, pinned above the vitals grid. Pulses until acknowledged.
 * @startingPoint section="Monitoring" subtitle="Active alert banner" viewport="700x140"
 */
export interface AlertBannerProps {
  level?: "warning" | "critical";
  message: string;
  /** Detector that raised it: "radar", "audio", "bcg". */
  source?: string;
  /** Preformatted clock time, e.g. "2:14 AM". */
  time?: string;
  acknowledged?: boolean;
  /** lucide icon node — XCircle for critical, AlertTriangle for warning. */
  icon?: React.ReactNode;
  onAcknowledge?: () => void;
  onResolve?: () => void;
}

export declare function AlertBanner(props: AlertBannerProps): JSX.Element;
