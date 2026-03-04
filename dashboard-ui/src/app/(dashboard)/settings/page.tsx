"use client";

import { useState } from "react";
import { useQuery } from "convex/react";
import { api } from "../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Wifi, HardDrive, Clock, RotateCw } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const systemHealth = useQuery(api.system.getHealth);
  const [restarting, setRestarting] = useState<Record<string, boolean>>({});

  const handleRestart = async (name: string) => {
    setRestarting((prev) => ({ ...prev, [name]: true }));
    try {
      const res = await fetch(`/api/sensors/${name}/restart`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        console.error("Restart failed:", body.detail ?? res.statusText);
      }
    } catch (e) {
      console.error("Restart request failed:", e);
    } finally {
      setTimeout(() => setRestarting((prev) => ({ ...prev, [name]: false })), 2000);
    }
  };

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
              ([name, info]) => {
                const status = (info as { status: string }).status;
                const isRestarting = restarting[name] ?? false;
                return (
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
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRestart(name)}
                        disabled={isRestarting}
                        className="p-1.5 rounded-md hover:bg-muted transition-colors disabled:opacity-50"
                        title={`Restart ${name} detector`}
                      >
                        <RotateCw
                          className={cn(
                            "h-4 w-4 text-muted-foreground",
                            isRestarting && "animate-spin"
                          )}
                        />
                      </button>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          status === "online"
                            ? "bg-success/20 text-success"
                            : status === "error"
                              ? "bg-danger/20 text-danger"
                              : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {status}
                      </span>
                    </div>
                  </div>
                );
              }
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
