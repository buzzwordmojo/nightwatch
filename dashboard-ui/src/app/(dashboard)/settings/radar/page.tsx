"use client";

import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RadarSignalChart } from "@/components/dashboard/RadarSignalChart";
import { RadarAimingView } from "@/components/dashboard/RadarAimingView";
import { Radio, Activity, Trash2 } from "lucide-react";

export default function RadarSettingsPage() {
  const vitals = useQuery(api.vitals.getCurrentVitals);
  const cleanupRadarSignal = useMutation(api.vitals.cleanupRadarSignal);

  // Get radar detector info
  const radarDetector = vitals?.detectors?.radar;
  const isConnected = radarDetector?.state !== undefined;
  const respirationRate = radarDetector?.value?.respiration_rate ?? null;
  const distance = radarDetector?.value?.target_distance ?? null;
  const presence = radarDetector?.value?.presence ?? false;

  const handleCleanup = async () => {
    try {
      const result = await cleanupRadarSignal({ keepHours: 1 });
      console.log(`Cleaned up ${result.deleted} old samples`);
    } catch (e) {
      console.error("Failed to cleanup:", e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Radar Sensor</h2>
        <p className="text-sm text-muted-foreground">
          HLK-LD2450 mmWave radar for breathing detection and presence monitoring
        </p>
      </div>

      {/* Status Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium flex items-center gap-2">
              <Radio className="h-4 w-4" />
              Radar Status
            </h3>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                isConnected
                  ? "bg-green-500/20 text-green-500"
                  : "bg-red-500/20 text-red-500"
              }`}
            >
              {isConnected ? "Connected" : "Disconnected"}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground">Presence</p>
              <p className="text-lg font-medium">
                {presence ? "Detected" : "None"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Distance</p>
              <p className="text-lg font-medium">
                {distance !== null ? `${distance} m` : "--"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Breathing Rate</p>
              <p className="text-lg font-medium">
                {respirationRate !== null
                  ? `${Math.round(respirationRate)} BPM`
                  : "--"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">State</p>
              <p className="text-lg font-medium capitalize">
                {radarDetector?.state ?? "--"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Aiming View */}
      <Card>
        <CardContent className="p-6">
          <RadarAimingView width={340} height={280} />
        </CardContent>
      </Card>

      {/* Signal Chart */}
      <Card>
        <CardContent className="p-6">
          <RadarSignalChart seconds={30} showSmoothed={true} />
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-3">
            <Activity className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>
                <strong className="text-foreground">Signal Processing:</strong>{" "}
                The radar outputs position data at ~11 Hz. Breathing is detected
                by analyzing Y-position (depth) variations caused by chest
                movement.
              </p>
              <p>
                <strong className="text-foreground">Optimal Placement:</strong>{" "}
                Position the radar 1-3 meters from the subject, pointed at their
                chest. The green zone in the aiming view shows optimal range.
              </p>
              <p>
                <strong className="text-foreground">Signal Quality:</strong>{" "}
                Standard deviation (std dev) indicates signal variability.
                Values of 5-15mm during normal breathing indicate good signal
                quality.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Maintenance */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Data Cleanup</h3>
              <p className="text-sm text-muted-foreground">
                Remove old radar signal data to free up storage
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={handleCleanup}>
              <Trash2 className="h-4 w-4 mr-2" />
              Clean old data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
