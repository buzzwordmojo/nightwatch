"use client";

import { useQuery } from "convex/react";
import { api } from "../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Wifi, HardDrive, Clock } from "lucide-react";

export default function SettingsPage() {
  const systemHealth = useQuery(api.system.getHealth);

  const formatUptime = (lastUpdate: number) => {
    if (!lastUpdate) return "Unknown";
    const now = Date.now();
    const diff = now - lastUpdate;
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    return `${Math.floor(diff / 3600000)} hours ago`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">General Settings</h2>
        <p className="text-sm text-muted-foreground">
          System status and device information
        </p>
      </div>

      {/* System Status */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-medium mb-4">System Status</h3>
          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-muted">
                  <Wifi className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">Connection</p>
                  <p className="text-sm text-muted-foreground">
                    Backend status
                  </p>
                </div>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${
                  systemHealth?.overall === "online"
                    ? "bg-success/20 text-success"
                    : systemHealth?.overall === "stale"
                      ? "bg-warning/20 text-warning"
                      : "bg-danger/20 text-danger"
                }`}
              >
                {systemHealth?.overall ?? "Unknown"}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-muted">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">Last Update</p>
                  <p className="text-sm text-muted-foreground">
                    Most recent data received
                  </p>
                </div>
              </div>
              <span className="text-sm text-muted-foreground">
                {formatUptime(systemHealth?.lastUpdate ?? 0)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-muted">
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">Detectors</p>
                  <p className="text-sm text-muted-foreground">
                    Active sensor count
                  </p>
                </div>
              </div>
              <span className="text-sm text-muted-foreground">
                {Object.keys(systemHealth?.components ?? {}).length} active
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detector Details */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-medium mb-4">Detector Status</h3>
          <div className="space-y-3">
            {Object.entries(systemHealth?.components ?? {}).map(
              ([name, info]) => (
                <div
                  key={name}
                  className="flex items-center justify-between py-2 border-b last:border-0"
                >
                  <div>
                    <p className="font-medium capitalize">{name}</p>
                    {(info as { message?: string }).message && (
                      <p className="text-sm text-muted-foreground">
                        {(info as { message?: string }).message}
                      </p>
                    )}
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      (info as { status: string }).status === "online"
                        ? "bg-success/20 text-success"
                        : (info as { status: string }).status === "error"
                          ? "bg-danger/20 text-danger"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {(info as { status: string }).status}
                  </span>
                </div>
              )
            )}

            {Object.keys(systemHealth?.components ?? {}).length === 0 && (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No detectors connected
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Version info */}
      <p className="text-xs text-muted-foreground text-center">
        Nightwatch v0.1.0
      </p>
    </div>
  );
}
