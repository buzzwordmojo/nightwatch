"use client";

import { cn } from "@/lib/utils";

interface StatusIndicatorProps {
  status: string;
  label?: string;
  size?: "sm" | "md" | "lg";
}

export function StatusIndicator({
  status,
  label,
  size = "md",
}: StatusIndicatorProps) {
  const getStatusColor = () => {
    switch (status) {
      case "online":
      case "normal":
        return "bg-success";
      case "warning":
      case "degraded":
        return "bg-warning";
      case "error":
      case "alert":
      case "critical":
      case "offline":
        return "bg-danger";
      case "stale":
        return "bg-warning animate-pulse";
      default:
        return "bg-muted-foreground";
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case "sm":
        return "h-2 w-2";
      case "lg":
        return "h-4 w-4";
      default:
        return "h-3 w-3";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "rounded-full",
          getSizeStyles(),
          getStatusColor(),
          status === "normal" || status === "online" ? "animate-pulse-ring" : ""
        )}
      />
      {label && (
        <span className="text-sm text-muted-foreground capitalize">
          {label}: {status}
        </span>
      )}
    </div>
  );
}
