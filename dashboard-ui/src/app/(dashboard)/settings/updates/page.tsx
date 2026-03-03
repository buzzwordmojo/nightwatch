"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Download,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  GitCommit,
  Clock,
} from "lucide-react";

export default function UpdatesSettingsPage() {
  const updateSettings = useQuery(api.settings.getUpdateSettings);
  const setSetting = useMutation(api.settings.set);
  const setUpdateStatus = useMutation(api.settings.setUpdateStatus);

  const [checking, setChecking] = useState(false);
  const [applying, setApplying] = useState(false);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [pollStatus, setPollStatus] = useState<string>("idle");
  const logRef = useRef<HTMLDivElement>(null);
  const pollInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const autoUpdate = updateSettings?.auto_update ?? true;

  const handleToggleAutoUpdate = async () => {
    await setSetting({ key: "update.auto_update", value: !autoUpdate });
  };

  const handleCheckUpdates = async () => {
    setChecking(true);
    try {
      await setUpdateStatus({ status: "checking", message: "Checking for updates..." });
      const resp = await fetch("/api/update/check", { method: "POST" });
      const data = await resp.json();

      await setUpdateStatus({
        status: "idle",
        message: data.available
          ? `${data.commitsBehind} update${data.commitsBehind === 1 ? "" : "s"} available`
          : "Up to date",
        available: data.available ?? false,
        current_commit: data.currentCommit ?? "",
        latest_commit: data.latestCommit ?? "",
        last_check: Date.now(),
      });
    } catch (e) {
      await setUpdateStatus({
        status: "error",
        message: `Check failed: ${e instanceof Error ? e.message : String(e)}`,
      });
    } finally {
      setChecking(false);
    }
  };

  const stopPolling = useCallback(() => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollInterval.current = setInterval(async () => {
      try {
        const resp = await fetch("/api/update/status");
        const data = await resp.json();
        setLogLines(data.lines || []);
        setPollStatus(data.status);

        if (data.complete) {
          stopPolling();
          setApplying(false);
          // Service will restart — reload after a delay
          setTimeout(() => window.location.reload(), 5000);
        }
      } catch {
        // Server might be restarting
      }
    }, 2000);
  }, [stopPolling]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logLines]);

  const handleApplyUpdate = async () => {
    setApplying(true);
    setLogLines([]);
    setPollStatus("updating");
    try {
      await setUpdateStatus({ status: "updating", message: "Applying update..." });
      await fetch("/api/update/apply", { method: "POST" });
      startPolling();
    } catch (e) {
      setApplying(false);
      await setUpdateStatus({
        status: "error",
        message: `Update failed: ${e instanceof Error ? e.message : String(e)}`,
      });
    }
  };

  const isUpdating = applying || pollStatus === "updating";
  const isComplete = pollStatus === "complete";
  const isError = pollStatus === "error" && !applying;

  const lastCheckStr = updateSettings?.last_check
    ? new Date(updateSettings.last_check).toLocaleString()
    : "Never";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Software Updates</h2>
        <p className="text-sm text-muted-foreground">
          Check for and apply over-the-air updates
        </p>
      </div>

      {/* Current Version */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <GitCommit className="h-5 w-5 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Current Version</h3>
                <p className="text-sm text-muted-foreground font-mono">
                  {updateSettings?.current_commit || "Unknown"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Last checked: {lastCheckStr}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Update Status */}
      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Update Status</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {updateSettings?.message || "No status"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {updateSettings?.available && !isUpdating && !isComplete && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full font-medium">
                  Update available
                </span>
              )}
              {isComplete && (
                <span className="text-xs bg-green-500/10 text-green-500 px-2 py-1 rounded-full font-medium flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Complete
                </span>
              )}
              {isError && (
                <span className="text-xs bg-red-500/10 text-red-500 px-2 py-1 rounded-full font-medium flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Error
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleCheckUpdates}
              disabled={checking || isUpdating}
            >
              {checking ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Check for Updates
            </Button>

            {updateSettings?.available && !isComplete && (
              <Button
                onClick={handleApplyUpdate}
                disabled={isUpdating}
              >
                {isUpdating ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Updating...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Update Now
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Commit info */}
          {updateSettings?.available && updateSettings.latest_commit && (
            <div className="text-sm text-muted-foreground">
              <span className="font-mono">{updateSettings.current_commit}</span>
              {" → "}
              <span className="font-mono">{updateSettings.latest_commit}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Update Log */}
      {logLines.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-medium mb-3">Update Log</h3>
            <div
              ref={logRef}
              className="bg-secondary/50 rounded-md p-4 max-h-64 overflow-y-auto font-mono text-xs leading-relaxed"
            >
              {logLines.map((line, i) => (
                <div
                  key={i}
                  className={
                    line.includes("ERROR")
                      ? "text-red-400"
                      : line.includes("DONE") || line.includes("COMPLETE")
                        ? "text-green-400"
                        : line.includes("STEP")
                          ? "text-blue-400"
                          : "text-muted-foreground"
                  }
                >
                  {line}
                </div>
              ))}
            </div>
            {isComplete && (
              <p className="text-sm text-muted-foreground mt-3">
                Update complete. Page will reload automatically...
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Auto-Update Toggle */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Auto-Update</h3>
              <p className="text-sm text-muted-foreground">
                Automatically check for and apply updates every 5 minutes
              </p>
            </div>
            <Button
              variant={autoUpdate ? "default" : "outline"}
              size="sm"
              onClick={handleToggleAutoUpdate}
            >
              {autoUpdate ? "Enabled" : "Disabled"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
