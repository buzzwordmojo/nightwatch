/** Determinate progress track — setup wizard steps, signal strength, update download. */
export interface ProgressProps {
  /** 0–100. */
  value: number;
  tone?: "accent" | "normal" | "warning" | "critical";
  /** Track height in px. Default 8. */
  height?: number;
  style?: React.CSSProperties;
}

export declare function Progress(props: ProgressProps): JSX.Element;
