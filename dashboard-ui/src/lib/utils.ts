import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }
  return `${seconds}s`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "normal":
      return "text-success";
    case "warning":
      return "text-warning";
    case "alert":
    case "critical":
      return "text-danger";
    default:
      return "text-muted-foreground";
  }
}

export function getStatusBgColor(status: string): string {
  switch (status) {
    case "normal":
      return "bg-success/20";
    case "warning":
      return "bg-warning/20";
    case "alert":
    case "critical":
      return "bg-danger/20";
    default:
      return "bg-muted";
  }
}
