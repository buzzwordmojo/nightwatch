"use client";

import { useMutation } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { Button } from "@/components/ui/button";
import { cn, formatTime } from "@/lib/utils";
import { AlertTriangle, XCircle, Check } from "lucide-react";

interface Alert {
  _id: string;
  alertId: string;
  level: string;
  source: string;
  message: string;
  triggeredAt: number;
  acknowledgedAt?: number;
  resolved: boolean;
}

interface AlertBannerProps {
  alert: Alert;
}

export function AlertBanner({ alert }: AlertBannerProps) {
  const acknowledge = useMutation(api.alerts.acknowledge);
  const resolve = useMutation(api.alerts.resolve);

  const isCritical = alert.level === "critical";
  const isAcknowledged = !!alert.acknowledgedAt;

  return (
    <div
      className={cn(
        "flex items-center justify-between p-4 rounded-lg border",
        isCritical
          ? "bg-danger/20 border-danger/50"
          : "bg-warning/20 border-warning/50",
        !isAcknowledged && "alert-pulse"
      )}
    >
      <div className="flex items-center gap-3">
        {isCritical ? (
          <XCircle className="h-6 w-6 text-danger" />
        ) : (
          <AlertTriangle className="h-6 w-6 text-warning" />
        )}

        <div>
          <p
            className={cn(
              "font-medium",
              isCritical ? "text-danger" : "text-warning"
            )}
          >
            {alert.message}
          </p>
          <p className="text-sm text-muted-foreground">
            {alert.source} • {formatTime(alert.triggeredAt)}
            {isAcknowledged && " • Acknowledged"}
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        {!isAcknowledged && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => acknowledge({ alertId: alert.alertId })}
          >
            <Check className="h-4 w-4 mr-1" />
            Acknowledge
          </Button>
        )}
        <Button
          variant={isCritical ? "danger" : "warning"}
          size="sm"
          onClick={() => resolve({ alertId: alert.alertId })}
        >
          Resolve
        </Button>
      </div>
    </div>
  );
}
