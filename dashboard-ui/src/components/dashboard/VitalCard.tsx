"use client";

import { ReactNode } from "react";
import { Card, CardContent, type CardProps } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface VitalCardProps {
  title: string;
  value: number | string | null | undefined;
  unit?: string;
  icon: ReactNode;
  status: string;
  isLoading?: boolean;
  normalRange?: { min: number; max: number };
  warningRange?: { low: number; high: number };
  criticalRange?: { low: number; high: number };
  showAsText?: boolean;
}

// Map status string to Card variant
function getCardVariant(status: string): CardProps["variant"] {
  switch (status) {
    case "normal":
      return "success";
    case "warning":
      return "warning";
    case "alert":
    case "critical":
      return "critical";
    default:
      return "default";
  }
}

export function VitalCard({
  title,
  value,
  unit,
  icon,
  status,
  isLoading,
  normalRange,
  warningRange,
  criticalRange,
  showAsText,
}: VitalCardProps) {
  // Derive status from value if ranges provided
  const derivedStatus = (() => {
    if (typeof value !== "number") return status;

    if (criticalRange) {
      if (value < criticalRange.low || value > criticalRange.high) {
        return "critical";
      }
    }
    if (warningRange) {
      if (value < warningRange.low || value > warningRange.high) {
        return "warning";
      }
    }
    if (normalRange) {
      if (value >= normalRange.min && value <= normalRange.max) {
        return "normal";
      }
    }
    return status;
  })();

  const getValueColor = () => {
    if (showAsText) {
      return derivedStatus === "normal" ? "text-success" : "text-muted-foreground";
    }

    if (typeof value !== "number" || !normalRange) {
      return "text-foreground";
    }

    if (derivedStatus === "critical") return "text-danger";
    if (derivedStatus === "warning") return "text-warning";
    if (value >= normalRange.min && value <= normalRange.max) return "text-success";

    return "text-foreground";
  };

  const displayValue = () => {
    if (isLoading) return "—";
    if (value === null || value === undefined) return "—";
    if (typeof value === "string") return value;
    return Math.round(value);
  };

  return (
    <Card variant={getCardVariant(derivedStatus)}>
      <CardContent className="p-3 sm:p-6">
        <div className="flex items-center justify-between mb-1 sm:mb-2">
          <span className="text-xs sm:text-sm text-muted-foreground">{title}</span>
          <span
            className={cn(
              "p-1.5 sm:p-2 rounded-full",
              derivedStatus === "normal" && "bg-success/20 text-success",
              derivedStatus === "warning" && "bg-warning/20 text-warning",
              (derivedStatus === "alert" || derivedStatus === "critical") && "bg-danger/20 text-danger",
              derivedStatus === "uncertain" && "bg-muted text-muted-foreground"
            )}
          >
            {icon}
          </span>
        </div>

        <div className="flex items-baseline gap-1 sm:gap-2">
          <span
            className={cn(
              "text-2xl sm:text-4xl font-bold tabular-nums",
              getValueColor(),
              isLoading && "animate-pulse"
            )}
          >
            {displayValue()}
          </span>
          {unit && !showAsText && (
            <span className="text-sm sm:text-lg text-muted-foreground">{unit}</span>
          )}
        </div>

        {normalRange && typeof value === "number" && (
          <p className="hidden sm:block text-xs text-muted-foreground mt-2">
            Normal: {normalRange.min}–{normalRange.max} {unit}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
