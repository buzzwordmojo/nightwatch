"use client";

import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface VitalCardProps {
  title: string;
  value: number | string | null | undefined;
  unit?: string;
  icon: ReactNode;
  status: string;
  isLoading?: boolean;
  normalRange?: { min: number; max: number };
  showAsText?: boolean;
}

export function VitalCard({
  title,
  value,
  unit,
  icon,
  status,
  isLoading,
  normalRange,
  showAsText,
}: VitalCardProps) {
  const getStatusStyles = () => {
    switch (status) {
      case "normal":
        return "border-success/50 breathing-glow";
      case "warning":
        return "border-warning/50 bg-warning/5";
      case "alert":
      case "critical":
        return "border-danger/50 bg-danger/5 alert-pulse";
      default:
        return "border-muted";
    }
  };

  const getValueColor = () => {
    if (showAsText) {
      return status === "normal" ? "text-success" : "text-muted-foreground";
    }

    if (typeof value !== "number" || !normalRange) {
      return "text-foreground";
    }

    if (value < normalRange.min || value > normalRange.max) {
      return "text-warning";
    }

    return "text-success";
  };

  const displayValue = () => {
    if (isLoading) return "—";
    if (value === null || value === undefined) return "—";
    if (typeof value === "string") return value;
    return Math.round(value);
  };

  return (
    <Card className={cn("transition-all duration-300", getStatusStyles())}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">{title}</span>
          <span
            className={cn(
              "p-2 rounded-full",
              status === "normal" && "bg-success/20 text-success",
              status === "warning" && "bg-warning/20 text-warning",
              status === "alert" && "bg-danger/20 text-danger",
              status === "uncertain" && "bg-muted text-muted-foreground"
            )}
          >
            {icon}
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span
            className={cn(
              "text-4xl font-bold tabular-nums",
              getValueColor(),
              isLoading && "animate-pulse"
            )}
          >
            {displayValue()}
          </span>
          {unit && !showAsText && (
            <span className="text-lg text-muted-foreground">{unit}</span>
          )}
        </div>

        {normalRange && typeof value === "number" && (
          <p className="text-xs text-muted-foreground mt-2">
            Normal: {normalRange.min}–{normalRange.max} {unit}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
