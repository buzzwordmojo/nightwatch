"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { VitalCard } from "@/components/dashboard/VitalCard";
import { StatusIndicator } from "@/components/dashboard/StatusIndicator";
import { AlertBanner } from "@/components/dashboard/AlertBanner";
import { VitalsChart } from "@/components/dashboard/VitalsChart";
import { PauseButton } from "@/components/dashboard/PauseButton";
import { Heart, Wind, Activity, Moon } from "lucide-react";
import { formatTime } from "@/lib/utils";

export default function Dashboard() {
  const vitals = useQuery(api.vitals.getCurrentVitals);
  const readings = useQuery(api.vitals.getRecentReadings, { minutes: 30 });
  const activeAlerts = useQuery(api.alerts.getActive);
  const pauseStatus = useQuery(api.system.isPaused);
  const systemHealth = useQuery(api.system.getHealth);

  const isLoading = vitals === undefined;

  return (
    <main className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Moon className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Nightwatch</h1>
            <p className="text-sm text-muted-foreground">
              {vitals ? `Last update: ${formatTime(vitals.timestamp)}` : "Connecting..."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusIndicator
            status={systemHealth?.overall ?? "offline"}
            label="System"
          />
          <PauseButton
            isPaused={pauseStatus?.paused ?? false}
            remainingMinutes={pauseStatus?.remainingMinutes}
          />
        </div>
      </header>

      {/* Active Alerts */}
      {activeAlerts && activeAlerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {activeAlerts.map((alert) => (
            <AlertBanner key={alert._id} alert={alert} />
          ))}
        </div>
      )}

      {/* Pause Banner */}
      {pauseStatus?.paused && (
        <div className="mb-6 p-4 rounded-lg bg-warning/20 border border-warning/50 text-center">
          <p className="text-warning font-medium">
            Monitoring paused for {pauseStatus.remainingMinutes} more minutes
          </p>
        </div>
      )}

      {/* Vitals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <VitalCard
          title="Heart Rate"
          value={vitals?.heartRate}
          unit="BPM"
          icon={<Heart className="h-5 w-5" />}
          status={vitals?.detectors?.bcg?.state ?? "uncertain"}
          isLoading={isLoading}
          normalRange={{ min: 50, max: 100 }}
          warningRange={{ low: 40, high: 120 }}
          criticalRange={{ low: 35, high: 150 }}
        />

        <VitalCard
          title="Respiration"
          value={vitals?.respirationRate}
          unit="BPM"
          icon={<Wind className="h-5 w-5" />}
          status={vitals?.detectors?.radar?.state ?? "uncertain"}
          isLoading={isLoading}
          normalRange={{ min: 10, max: 25 }}
          warningRange={{ low: 6, high: 30 }}
          criticalRange={{ low: 4, high: 35 }}
        />

        <VitalCard
          title="Breathing"
          value={vitals?.breathingDetected ? "Detected" : "—"}
          icon={<Activity className="h-5 w-5" />}
          status={vitals?.detectors?.audio?.state ?? "uncertain"}
          isLoading={isLoading}
          showAsText
        />

        <VitalCard
          title="Bed Status"
          value={vitals?.bedOccupied ? "Occupied" : "Empty"}
          icon={<Moon className="h-5 w-5" />}
          status={vitals?.bedOccupied ? "normal" : "uncertain"}
          isLoading={isLoading}
          showAsText
        />
      </div>

      {/* Chart */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">Vitals History (30 min)</h2>
        <VitalsChart data={readings ?? []} />
      </div>

      {/* Detector Status */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        {["radar", "audio", "bcg"].map((detector) => {
          const d = vitals?.detectors?.[detector];
          return (
            <div
              key={detector}
              className="rounded-lg border bg-card p-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium capitalize">{detector} Detector</p>
                <p className="text-sm text-muted-foreground">
                  Confidence: {d?.confidence ? `${Math.round(d.confidence * 100)}%` : "—"}
                </p>
              </div>
              <StatusIndicator status={d?.state ?? "offline"} />
            </div>
          );
        })}
      </div>
    </main>
  );
}
