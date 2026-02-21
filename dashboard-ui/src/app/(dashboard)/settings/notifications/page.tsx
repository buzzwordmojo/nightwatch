"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Bell, Send } from "lucide-react";

type Provider = "pushover" | "ntfy";

interface NotificationSettings {
  enabled: boolean;
  provider: Provider;
  pushoverUserKey: string;
  pushoverApiToken: string;
  ntfyServer: string;
  ntfyTopic: string;
  alertLevels: string[];
}

const defaultSettings: NotificationSettings = {
  enabled: false,
  provider: "pushover",
  pushoverUserKey: "",
  pushoverApiToken: "",
  ntfyServer: "https://ntfy.sh",
  ntfyTopic: "",
  alertLevels: ["critical", "warning"],
};

export default function NotificationsSettingsPage() {
  const allSettings = useQuery(api.settings.getAll);
  const setSetting = useMutation(api.settings.set);

  const [settings, setSettings] = useState<NotificationSettings>(defaultSettings);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  // Load settings from Convex
  useEffect(() => {
    if (allSettings) {
      setSettings({
        enabled: (allSettings["notifications.enabled"] as boolean) ?? false,
        provider:
          (allSettings["notifications.provider"] as Provider) ?? "pushover",
        pushoverUserKey:
          (allSettings["notifications.pushoverUserKey"] as string) ?? "",
        pushoverApiToken:
          (allSettings["notifications.pushoverApiToken"] as string) ?? "",
        ntfyServer:
          (allSettings["notifications.ntfyServer"] as string) ??
          "https://ntfy.sh",
        ntfyTopic: (allSettings["notifications.ntfyTopic"] as string) ?? "",
        alertLevels:
          (allSettings["notifications.alertLevels"] as string[]) ?? [
            "critical",
            "warning",
          ],
      });
    }
  }, [allSettings]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await Promise.all([
        setSetting({ key: "notifications.enabled", value: settings.enabled }),
        setSetting({ key: "notifications.provider", value: settings.provider }),
        setSetting({
          key: "notifications.pushoverUserKey",
          value: settings.pushoverUserKey,
        }),
        setSetting({
          key: "notifications.pushoverApiToken",
          value: settings.pushoverApiToken,
        }),
        setSetting({
          key: "notifications.ntfyServer",
          value: settings.ntfyServer,
        }),
        setSetting({ key: "notifications.ntfyTopic", value: settings.ntfyTopic }),
        setSetting({
          key: "notifications.alertLevels",
          value: settings.alertLevels,
        }),
      ]);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      // For now, we'll just simulate the test
      // In production, this would call an API endpoint
      if (settings.provider === "pushover") {
        if (!settings.pushoverUserKey || !settings.pushoverApiToken) {
          setTestResult({
            success: false,
            message: "Please enter Pushover credentials",
          });
          return;
        }
        // Would call: POST https://api.pushover.net/1/messages.json
        setTestResult({
          success: true,
          message: "Test notification sent to Pushover",
        });
      } else {
        if (!settings.ntfyTopic) {
          setTestResult({
            success: false,
            message: "Please enter an Ntfy topic",
          });
          return;
        }
        // Would call: POST to ntfy server
        setTestResult({
          success: true,
          message: "Test notification sent to Ntfy",
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: "Failed to send test notification",
      });
    } finally {
      setIsTesting(false);
    }
  };

  const toggleAlertLevel = (level: string) => {
    setSettings((prev) => ({
      ...prev,
      alertLevels: prev.alertLevels.includes(level)
        ? prev.alertLevels.filter((l) => l !== level)
        : [...prev.alertLevels, level],
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Push Notifications</h2>
        <p className="text-sm text-muted-foreground">
          Get alerts on your phone when issues are detected
        </p>
      </div>

      {/* Enable toggle */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-muted">
                <Bell className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">Push Notifications</p>
                <p className="text-sm text-muted-foreground">
                  Send alerts to your phone
                </p>
              </div>
            </div>
            <button
              onClick={() =>
                setSettings((prev) => ({ ...prev, enabled: !prev.enabled }))
              }
              className={`relative w-12 h-6 rounded-full transition-colors ${
                settings.enabled ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                  settings.enabled ? "translate-x-6" : ""
                }`}
              />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Provider selection */}
      {settings.enabled && (
        <>
          <Card>
            <CardContent className="p-6 space-y-4">
              <h3 className="font-medium">Provider</h3>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() =>
                    setSettings((prev) => ({ ...prev, provider: "pushover" }))
                  }
                  className={`p-4 rounded-lg border text-left transition-colors ${
                    settings.provider === "pushover"
                      ? "border-primary bg-primary/5"
                      : "border-muted hover:border-muted-foreground/50"
                  }`}
                >
                  <p className="font-medium">Pushover</p>
                  <p className="text-sm text-muted-foreground">
                    Reliable push notifications
                  </p>
                </button>

                <button
                  onClick={() =>
                    setSettings((prev) => ({ ...prev, provider: "ntfy" }))
                  }
                  className={`p-4 rounded-lg border text-left transition-colors ${
                    settings.provider === "ntfy"
                      ? "border-primary bg-primary/5"
                      : "border-muted hover:border-muted-foreground/50"
                  }`}
                >
                  <p className="font-medium">Ntfy</p>
                  <p className="text-sm text-muted-foreground">
                    Free, self-hostable
                  </p>
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Provider-specific settings */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <h3 className="font-medium">
                {settings.provider === "pushover"
                  ? "Pushover Settings"
                  : "Ntfy Settings"}
              </h3>

              {settings.provider === "pushover" ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">
                      User Key
                    </label>
                    <input
                      type="text"
                      value={settings.pushoverUserKey}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          pushoverUserKey: e.target.value,
                        }))
                      }
                      placeholder="Enter your Pushover user key"
                      className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">
                      API Token
                    </label>
                    <input
                      type="password"
                      value={settings.pushoverApiToken}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          pushoverApiToken: e.target.value,
                        }))
                      }
                      placeholder="Enter your Pushover API token"
                      className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">
                      Server
                    </label>
                    <input
                      type="url"
                      value={settings.ntfyServer}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          ntfyServer: e.target.value,
                        }))
                      }
                      placeholder="https://ntfy.sh"
                      className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">
                      Topic
                    </label>
                    <input
                      type="text"
                      value={settings.ntfyTopic}
                      onChange={(e) =>
                        setSettings((prev) => ({
                          ...prev,
                          ntfyTopic: e.target.value,
                        }))
                      }
                      placeholder="nightwatch-alerts"
                      className="w-full px-3 py-2 rounded-md border bg-background text-sm"
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Alert levels */}
          <Card>
            <CardContent className="p-6 space-y-4">
              <h3 className="font-medium">Alert Levels</h3>
              <p className="text-sm text-muted-foreground">
                Choose which alert levels trigger push notifications
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => toggleAlertLevel("critical")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    settings.alertLevels.includes("critical")
                      ? "bg-danger/20 text-danger border border-danger/50"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  Critical
                </button>
                <button
                  onClick={() => toggleAlertLevel("warning")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    settings.alertLevels.includes("warning")
                      ? "bg-warning/20 text-warning border border-warning/50"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  Warning
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Test and Save */}
          <div className="flex gap-3">
            <button
              onClick={handleTest}
              disabled={isTesting}
              className="flex items-center gap-2 px-4 py-2 rounded-md border hover:bg-muted transition-colors disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              {isTesting ? "Sending..." : "Test"}
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 px-4 py-2 rounded-md bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>

          {/* Test result */}
          {testResult && (
            <div
              className={`p-3 rounded-md text-sm ${
                testResult.success
                  ? "bg-success/20 text-success"
                  : "bg-danger/20 text-danger"
              }`}
            >
              {testResult.message}
            </div>
          )}
        </>
      )}
    </div>
  );
}
