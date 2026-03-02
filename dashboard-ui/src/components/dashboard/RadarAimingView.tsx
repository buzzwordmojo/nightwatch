"use client";

import { useRef, useEffect, useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "../../../convex/_generated/api";
import { cn } from "@/lib/utils";

interface RadarAimingViewProps {
  className?: string;
  width?: number;
  height?: number;
}

// Zone configuration: distance in meters
const ZONES = [
  { minDist: 0, maxDist: 0.5, color: "transparent", label: "Too close" },
  { minDist: 0.5, maxDist: 1, color: "#fbbf24", label: "0.5-1m (close)" },
  { minDist: 1, maxDist: 3, color: "#22c55e", label: "1-3m (optimal)" },
  { minDist: 3, maxDist: 4, color: "#fbbf24", label: "3-4m (far)" },
  { minDist: 4, maxDist: 6, color: "transparent", label: "Too far" },
];

export function RadarAimingView({
  className,
  width = 300,
  height = 300,
}: RadarAimingViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Query recent radar signal data (last 1 second for position)
  const signalData = useQuery(api.vitals.getRadarSignal, {
    seconds: 1,
    maxPoints: 20,
  });

  // Get latest position
  const latestPosition = useMemo(() => {
    if (!signalData || signalData.length === 0) return null;
    const latest = signalData[signalData.length - 1];
    return {
      x: latest.x / 1000, // Convert mm to m
      y: latest.y / 1000,
      distance: latest.distance,
    };
  }, [signalData]);

  // Draw radar view
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set up for high DPI
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Clear
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, width, height);

    // Center point (radar position)
    const centerX = width / 2;
    const centerY = height - 30; // Bottom-center for top-down view

    // Scale: 1 meter = pixels
    const scale = (height - 60) / 6; // 6 meters fits in view

    // Draw distance zones as arcs
    for (const zone of ZONES) {
      if (zone.color === "transparent") continue;

      const innerR = zone.minDist * scale;
      const outerR = zone.maxDist * scale;

      ctx.beginPath();
      ctx.arc(centerX, centerY, outerR, Math.PI, 0, false);
      ctx.arc(centerX, centerY, innerR, 0, Math.PI, true);
      ctx.closePath();

      ctx.fillStyle = zone.color + "20"; // 12% opacity
      ctx.fill();
      ctx.strokeStyle = zone.color + "60";
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw distance rings
    for (let d = 1; d <= 5; d++) {
      const r = d * scale;
      ctx.beginPath();
      ctx.arc(centerX, centerY, r, Math.PI, 0);
      ctx.strokeStyle = "#334155";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Distance label
      ctx.fillStyle = "#64748b";
      ctx.font = "10px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(`${d}m`, centerX, centerY - r - 4);
    }

    // Draw angle lines
    for (let angle = -60; angle <= 60; angle += 30) {
      const rad = (angle * Math.PI) / 180;
      const endX = centerX + Math.sin(rad) * scale * 5;
      const endY = centerY - Math.cos(rad) * scale * 5;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = "#334155";
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Draw radar icon at center
    ctx.beginPath();
    ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
    ctx.fillStyle = "#3b82f6";
    ctx.fill();

    // Label
    ctx.fillStyle = "#64748b";
    ctx.font = "11px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("Radar", centerX, centerY + 20);

    // Draw target if we have position data
    if (latestPosition) {
      const targetX = centerX + latestPosition.x * scale;
      const targetY = centerY - latestPosition.y * scale;

      // Determine zone color
      const dist = latestPosition.distance;
      let targetColor = "#ef4444"; // Red for out of range
      for (const zone of ZONES) {
        if (dist >= zone.minDist && dist < zone.maxDist) {
          targetColor =
            zone.color === "transparent" ? "#ef4444" : zone.color;
          break;
        }
      }

      // Draw target glow
      ctx.beginPath();
      ctx.arc(targetX, targetY, 20, 0, Math.PI * 2);
      ctx.fillStyle = targetColor + "30";
      ctx.fill();

      // Draw target
      ctx.beginPath();
      ctx.arc(targetX, targetY, 8, 0, Math.PI * 2);
      ctx.fillStyle = targetColor;
      ctx.fill();

      // Draw crosshair
      ctx.strokeStyle = targetColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(targetX - 15, targetY);
      ctx.lineTo(targetX - 8, targetY);
      ctx.moveTo(targetX + 8, targetY);
      ctx.lineTo(targetX + 15, targetY);
      ctx.moveTo(targetX, targetY - 15);
      ctx.lineTo(targetX, targetY - 8);
      ctx.moveTo(targetX, targetY + 8);
      ctx.lineTo(targetX, targetY + 15);
      ctx.stroke();

      // Distance label near target
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 12px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(`${dist.toFixed(2)}m`, targetX, targetY - 25);
    }
  }, [width, height, latestPosition]);

  // Determine status based on position
  const status = useMemo(() => {
    if (!latestPosition) return { text: "No target", color: "text-muted-foreground" };

    const dist = latestPosition.distance;
    if (dist < 0.5) return { text: "Too close", color: "text-red-500" };
    if (dist < 1) return { text: "Close range", color: "text-yellow-500" };
    if (dist < 3) return { text: "Optimal range", color: "text-green-500" };
    if (dist < 4) return { text: "Far range", color: "text-yellow-500" };
    return { text: "Too far", color: "text-red-500" };
  }, [latestPosition]);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div>
        <h3 className="text-base font-semibold">Radar Aiming</h3>
        <p className="text-xs text-muted-foreground">
          Top-down view showing target position and optimal zones
        </p>
      </div>

      {/* Canvas */}
      <div className="flex justify-center">
        <canvas
          ref={canvasRef}
          style={{ width, height }}
          className="rounded-lg border border-muted"
        />
      </div>

      {/* Status */}
      <div className="text-center">
        <span className={cn("font-medium", status.color)}>{status.text}</span>
        {latestPosition && (
          <span className="text-muted-foreground ml-2">
            ({latestPosition.distance.toFixed(2)}m at{" "}
            {Math.round(
              (Math.atan2(latestPosition.x, latestPosition.y) * 180) / Math.PI
            )}
            &deg;)
          </span>
        )}
      </div>

      {/* Zone legend */}
      <div className="flex justify-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-yellow-500/30 border border-yellow-500/60" />
          0.5-1m / 3-4m
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-green-500/30 border border-green-500/60" />
          1-3m (optimal)
        </span>
      </div>
    </div>
  );
}
