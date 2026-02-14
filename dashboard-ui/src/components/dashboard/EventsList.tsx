"use client";

import { useMemo } from "react";
import { cn, formatTime } from "@/lib/utils";
import { AlertTriangle, XCircle, Activity } from "lucide-react";

interface Alert {
  _id: string;
  alertId: string;
  level: string;
  source: string;
  message: string;
  triggeredAt: number;
  resolvedAt?: number;
  resolved: boolean;
}

interface EventPeriod {
  id: string;
  source: string;
  level: string;
  message: string;
  startTime: number;
  endTime?: number;
  duration: number;
  resolved: boolean;
  count: number;
}

interface EventsListProps {
  alerts: Alert[];
  showNormal?: boolean;
}

// Format duration in human-readable form
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

// Consolidate consecutive alerts into periods
function consolidateAlerts(alerts: Alert[]): EventPeriod[] {
  if (!alerts || alerts.length === 0) return [];

  // Filter out "normal" level alerts
  const filteredAlerts = alerts.filter(
    (a) => a.level !== "normal" && a.level !== "ok"
  );

  // Sort by time (oldest first for grouping)
  const sorted = [...filteredAlerts].sort(
    (a, b) => a.triggeredAt - b.triggeredAt
  );

  const periods: EventPeriod[] = [];
  let currentPeriod: EventPeriod | null = null;

  // Max gap to consider alerts as part of same period (30 seconds)
  const MAX_GAP_MS = 30 * 1000;

  for (const alert of sorted) {
    const shouldStartNewPeriod =
      !currentPeriod ||
      currentPeriod.source !== alert.source ||
      currentPeriod.level !== alert.level ||
      alert.triggeredAt - (currentPeriod.endTime || currentPeriod.startTime) >
        MAX_GAP_MS;

    if (shouldStartNewPeriod) {
      // Save current period if exists
      if (currentPeriod) {
        periods.push(currentPeriod);
      }

      // Start new period
      currentPeriod = {
        id: alert._id,
        source: alert.source,
        level: alert.level,
        message: alert.message,
        startTime: alert.triggeredAt,
        endTime: alert.resolvedAt || (alert.resolved ? alert.triggeredAt : undefined),
        duration: 0,
        resolved: alert.resolved,
        count: 1,
      };
    } else {
      // Extend current period
      currentPeriod.count++;
      currentPeriod.endTime = alert.resolvedAt || alert.triggeredAt;
      currentPeriod.resolved = alert.resolved;
    }
  }

  // Don't forget the last period
  if (currentPeriod) {
    periods.push(currentPeriod);
  }

  // Calculate durations and sort by most recent
  return periods
    .map((p) => ({
      ...p,
      duration: p.endTime ? p.endTime - p.startTime : Date.now() - p.startTime,
    }))
    .sort((a, b) => b.startTime - a.startTime);
}

// Get display name for source
function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    radar: "Breathing",
    audio: "Audio",
    bcg: "Heart Rate",
    movement: "Movement",
  };
  return labels[source] || source;
}

export function EventsList({ alerts, showNormal = false }: EventsListProps) {
  const periods = useMemo(() => consolidateAlerts(alerts), [alerts]);

  if (!periods || periods.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No alerts in the last 24 hours</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {periods.map((period) => {
        const isCritical = period.level === "critical" || period.level === "alert";
        const isOngoing = !period.resolved && !period.endTime;

        return (
          <div
            key={period.id}
            className={cn(
              "flex items-start gap-3 p-3 rounded-lg border transition-all",
              isCritical
                ? "bg-danger/10 border-danger/30"
                : "bg-warning/10 border-warning/30",
              isOngoing && "animate-pulse-slow"
            )}
          >
            {/* Icon */}
            <div
              className={cn(
                "p-2 rounded-full shrink-0",
                isCritical ? "bg-danger/20 text-danger" : "bg-warning/20 text-warning"
              )}
            >
              {isCritical ? (
                <XCircle className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span
                  className={cn(
                    "font-medium",
                    isCritical ? "text-danger" : "text-warning"
                  )}
                >
                  {getSourceLabel(period.source)}
                </span>
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full uppercase",
                    isCritical
                      ? "bg-danger/20 text-danger"
                      : "bg-warning/20 text-warning"
                  )}
                >
                  {period.level}
                </span>
              </div>

              <p className="text-sm text-muted-foreground mt-0.5 truncate">
                {period.message}
              </p>

              {/* Time info */}
              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                <span>{formatTime(period.startTime)}</span>
                {period.endTime && !isOngoing ? (
                  <>
                    <span>-</span>
                    <span>{formatTime(period.endTime)}</span>
                    <span className="text-foreground/60">
                      ({formatDuration(period.duration)})
                    </span>
                  </>
                ) : (
                  <span className={cn("font-medium", isCritical ? "text-danger" : "text-warning")}>
                    ongoing
                  </span>
                )}
                {period.count > 1 && (
                  <span className="text-foreground/40">
                    • {period.count} events
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
