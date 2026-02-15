"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../convex/_generated/api";
import { DashboardView } from "@/components/dashboard/DashboardView";
import { AlertTriangle, Pause, Play } from "lucide-react";

export default function SharedDashboard() {
  const params = useParams();
  const token = params.token as string;

  const validation = useQuery(api.sharing.validate, { token });
  const vitals = useQuery(api.vitals.getCurrentVitals);
  const readings = useQuery(api.vitals.getRecentReadings, { minutes: 480 });
  const activeAlerts = useQuery(api.alerts.getActive);
  const pauseStatus = useQuery(api.system.isPaused);
  const systemHealth = useQuery(api.system.getHealth);

  const pauseMutation = useMutation(api.system.pause);
  const resumeMutation = useMutation(api.system.resume);

  // Check validation
  if (validation === undefined) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </main>
    );
  }

  if (!validation.valid) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <div className="p-4 rounded-full bg-danger/20 inline-block mb-4">
            <AlertTriangle className="h-8 w-8 text-danger" />
          </div>
          <h1 className="text-xl font-semibold mb-2">Link Invalid</h1>
          <p className="text-muted-foreground">
            {validation.reason === "expired"
              ? "This share link has expired."
              : validation.reason === "revoked"
                ? "This share link has been revoked."
                : "This share link is not valid."}
          </p>
        </div>
      </main>
    );
  }

  const canPause = validation.permissions === "view+pause";

  const handlePause = async () => {
    await pauseMutation({ durationMinutes: 30 });
  };

  const handleResume = async () => {
    await resumeMutation({});
  };

  return (
    <DashboardView
      vitals={vitals}
      readings={readings}
      activeAlerts={activeAlerts}
      pauseStatus={pauseStatus}
      systemHealth={systemHealth}
      showDetectorStatus={false}
      headerExtra={
        <>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
            Shared view
          </span>
          {canPause && (
            <button
              onClick={pauseStatus?.paused ? handleResume : handlePause}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pauseStatus?.paused
                  ? "bg-warning/20 text-warning hover:bg-warning/30"
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              {pauseStatus?.paused ? (
                <>
                  <Play className="h-4 w-4" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="h-4 w-4" />
                  Pause
                </>
              )}
            </button>
          )}
        </>
      }
    />
  );
}
