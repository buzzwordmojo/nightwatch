"use client";

import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { DashboardView } from "@/components/dashboard/DashboardView";
import { PauseButton } from "@/components/dashboard/PauseButton";

export default function Dashboard() {
  const vitals = useQuery(api.vitals.getCurrentVitals);
  const readings = useQuery(api.vitals.getRecentReadings, { minutes: 480 });
  const activeAlerts = useQuery(api.alerts.getActive);
  const pauseStatus = useQuery(api.system.isPaused);
  const systemHealth = useQuery(api.system.getHealth);

  return (
    <DashboardView
      vitals={vitals}
      readings={readings}
      activeAlerts={activeAlerts}
      pauseStatus={pauseStatus}
      systemHealth={systemHealth}
      headerExtra={
        <PauseButton
          isPaused={pauseStatus?.paused ?? false}
          remainingMinutes={pauseStatus?.remainingMinutes}
        />
      }
      showDetectorStatus
    />
  );
}
