"use client";

import { Wifi, WifiOff, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Network } from "@/lib/wifi-api";

interface NetworkListProps {
  networks: Network[];
  selectedSsid: string | null;
  onSelect: (ssid: string) => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

function getSignalIcon(signal: number) {
  if (signal >= 70) return <Wifi className="h-4 w-4 text-success" />;
  if (signal >= 40) return <Wifi className="h-4 w-4 text-warning" />;
  return <WifiOff className="h-4 w-4 text-muted-foreground" />;
}

function getSignalLabel(signal: number) {
  if (signal >= 70) return "Strong";
  if (signal >= 40) return "Good";
  return "Weak";
}

export function NetworkList({
  networks,
  selectedSsid,
  onSelect,
  loading,
  error,
  onRetry,
}: NetworkListProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <div className="relative">
          <Wifi className="h-8 w-8 animate-pulse" />
          <div className="absolute inset-0 animate-ping">
            <Wifi className="h-8 w-8 opacity-30" />
          </div>
        </div>
        <p className="mt-4 text-sm">Scanning for networks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <WifiOff className="h-8 w-8 text-destructive" />
        <p className="mt-4 text-sm text-destructive">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 text-sm text-primary hover:underline"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  if (networks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
        <WifiOff className="h-8 w-8" />
        <p className="mt-4 text-sm">No networks found</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 text-sm text-primary hover:underline"
          >
            Scan again
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {networks.map((network) => (
        <button
          key={network.ssid}
          onClick={() => onSelect(network.ssid)}
          className={cn(
            "w-full p-4 rounded-lg flex items-center justify-between transition-all",
            "bg-card border border-border hover:border-primary/50 hover:bg-accent/50",
            selectedSsid === network.ssid &&
              "border-primary bg-primary/10 ring-2 ring-primary/20"
          )}
        >
          <div className="flex items-center gap-3">
            {getSignalIcon(network.signal)}
            <div className="text-left">
              <p className="font-medium">{network.ssid}</p>
              <p className="text-xs text-muted-foreground">
                {getSignalLabel(network.signal)} signal
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {network.security && network.security !== "open" && (
              <Lock className="h-3 w-3 text-muted-foreground" />
            )}
            <span className="text-sm text-muted-foreground">{network.signal}%</span>
          </div>
        </button>
      ))}
    </div>
  );
}
