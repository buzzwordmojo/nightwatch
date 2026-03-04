"use client";

import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Radio, Mic, Activity } from "lucide-react";

interface SensorStatus {
  connected: boolean;
  status: string;
  signal?: number;
  device?: string;
  error?: string;
  lastEvent?: number;
  uptime?: number;
}

interface SensorStatusBarProps {
  detectors?: {
    radar?: SensorStatus;
    audio?: SensorStatus;
    bcg?: SensorStatus;
  };
  mockComponents?: Record<string, { mock?: boolean }>;
}

const sensorConfig = [
  { key: "radar", label: "Radar", icon: Radio },
  { key: "audio", label: "Audio", icon: Mic },
  { key: "bcg", label: "BCG", icon: Activity },
] as const;

function getStatusColor(status?: SensorStatus): string {
  if (!status || !status.connected) {
    return "bg-muted-foreground/50"; // gray - offline
  }
  switch (status.status) {
    case "running":
    case "online":
    case "normal":
      return "bg-green-500"; // green - healthy
    case "warning":
    case "degraded":
    case "uncertain":
      return "bg-yellow-500"; // yellow - warning
    case "error":
    case "critical":
    case "alert":
      return "bg-red-500"; // red - error
    default:
      return "bg-muted-foreground/50"; // gray - unknown
  }
}

function formatUptime(seconds?: number): string {
  if (!seconds) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatLastEvent(timestamp?: number): string {
  if (!timestamp) return "—";
  const seconds = Math.round((Date.now() / 1000) - timestamp);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function SensorStatusBar({ detectors, mockComponents }: SensorStatusBarProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex items-center gap-1.5">
        {sensorConfig.map(({ key, label, icon: Icon }) => {
          const sensor = detectors?.[key as keyof typeof detectors];
          const isMock = mockComponents?.[key]?.mock ?? false;
          const statusColor = isMock ? "bg-purple-500" : getStatusColor(sensor);
          const isConnected = sensor?.connected ?? false;

          return (
            <Tooltip key={key}>
              <TooltipTrigger asChild>
                <button
                  className={cn(
                    "flex items-center gap-1 px-1.5 py-0.5 rounded text-xs transition-colors",
                    "hover:bg-accent/50",
                    isConnected ? "text-foreground" : "text-muted-foreground"
                  )}
                >
                  <span
                    className={cn(
                      "w-1.5 h-1.5 rounded-full shrink-0",
                      statusColor,
                      isConnected && (sensor?.status === "running" || sensor?.status === "normal") && !isMock && "animate-pulse"
                    )}
                  />
                  <Icon className="w-3 h-3 hidden sm:block" />
                  <span className="hidden md:inline">{label}</span>
                  {isMock && (
                    <span className="px-1 py-px text-[9px] font-bold leading-none rounded bg-purple-500 text-white">
                      SIM
                    </span>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[200px]">
                <div className="space-y-1">
                  <div className="font-medium flex items-center gap-2">
                    <Icon className="w-4 h-4" />
                    {label} Sensor
                  </div>
                  <div className="text-xs space-y-0.5 text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <span className={cn(
                        "capitalize",
                        isMock ? "text-purple-500" : isConnected ? "text-green-500" : "text-red-500"
                      )}>
                        {isMock ? "simulated" : isConnected ? (sensor?.status ?? "connected") : "offline"}
                      </span>
                    </div>
                    {sensor?.signal !== undefined && (
                      <div className="flex justify-between">
                        <span>Signal:</span>
                        <span>{sensor.signal}%</span>
                      </div>
                    )}
                    {sensor?.device && (
                      <div className="flex justify-between">
                        <span>Device:</span>
                        <span className="truncate max-w-[100px]">{sensor.device}</span>
                      </div>
                    )}
                    {sensor?.lastEvent && (
                      <div className="flex justify-between">
                        <span>Last event:</span>
                        <span>{formatLastEvent(sensor.lastEvent)}</span>
                      </div>
                    )}
                    {sensor?.uptime && (
                      <div className="flex justify-between">
                        <span>Uptime:</span>
                        <span>{formatUptime(sensor.uptime)}</span>
                      </div>
                    )}
                    {sensor?.error && (
                      <div className="text-red-400 mt-1">
                        {sensor.error}
                      </div>
                    )}
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
