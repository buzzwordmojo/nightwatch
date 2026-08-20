import * as React from "react";

/**
 * The dashboard's primary readout: one live vital per card. Status is derived from the
 * supplied ranges when the value is numeric, otherwise from `status`.
 * @startingPoint section="Monitoring" subtitle="Live vital readout card" viewport="700x220"
 */
export interface VitalCardProps {
  title: string;
  value: number | string | null;
  unit?: string;
  /** lucide icon node, 20×20. */
  icon?: React.ReactNode;
  status?: "normal" | "warning" | "alert" | "critical" | "uncertain" | string;
  isLoading?: boolean;
  normalRange?: { min: number; max: number };
  warningRange?: { low: number; high: number };
  criticalRange?: { low: number; high: number };
  /** Render the value as a word ("Occupied", "Detected") rather than a number. */
  showAsText?: boolean;
  /** Replaces the "Normal: x–y" caption, e.g. fusion agreement. */
  subtitle?: string;
}

export declare function VitalCard(props: VitalCardProps): JSX.Element;
