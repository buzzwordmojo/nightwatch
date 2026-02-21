"use client";

import { Loader2, CheckCircle2, XCircle, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";

export type ConnectionState = "idle" | "connecting" | "searching" | "success" | "error";

interface ConnectionStatusProps {
  state: ConnectionState;
  message?: string;
  progress?: {
    current: number;
    total: number;
  };
}

const stateConfig: Record<
  ConnectionState,
  { icon: React.ReactNode; color: string; defaultMessage: string }
> = {
  idle: {
    icon: <Wifi className="h-6 w-6" />,
    color: "text-muted-foreground",
    defaultMessage: "Ready to connect",
  },
  connecting: {
    icon: <Loader2 className="h-6 w-6 animate-spin" />,
    color: "text-primary",
    defaultMessage: "Connecting to network...",
  },
  searching: {
    icon: <Loader2 className="h-6 w-6 animate-spin" />,
    color: "text-primary",
    defaultMessage: "Searching for Nightwatch...",
  },
  success: {
    icon: <CheckCircle2 className="h-6 w-6" />,
    color: "text-success",
    defaultMessage: "Connected successfully!",
  },
  error: {
    icon: <XCircle className="h-6 w-6" />,
    color: "text-destructive",
    defaultMessage: "Connection failed",
  },
};

export function ConnectionStatus({ state, message, progress }: ConnectionStatusProps) {
  const config = stateConfig[state];

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className={cn("mb-4", config.color)}>{config.icon}</div>
      <p className={cn("text-sm font-medium", config.color)}>
        {message || config.defaultMessage}
      </p>
      {progress && state === "searching" && (
        <div className="mt-4 w-full max-w-xs">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Scanning network</span>
            <span>
              {Math.round((progress.current / progress.total) * 100)}%
            </span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
