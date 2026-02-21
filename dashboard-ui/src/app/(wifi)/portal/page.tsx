"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  NetworkList,
  PasswordInput,
  ConnectionStatus,
  useWifiSetup,
} from "@/components/wifi";
import { ArrowLeft, RefreshCw, Wifi } from "lucide-react";

// Portal page is served from the Pi itself, so use relative URLs
const PORTAL_URL = "";

export default function PortalPage() {
  const wifi = useWifiSetup({
    portalUrl: PORTAL_URL,
    deviceId: "Nightwatch",
    autoStart: true,
    skipHotspotDetection: true, // Already on hotspot when viewing portal
    skipDeviceSearch: true, // Browser will close after submit
  });

  // Calculate progress percentage (2 steps only: select network, connect)
  const getProgress = () => {
    switch (wifi.step) {
      case "select-network":
      case "entering-password":
        return 33;
      case "connecting":
        return 66;
      case "complete":
        return 100;
      default:
        return 0;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with icon */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Wifi className="h-8 w-8 text-primary" />
        </div>
        <p className="text-muted-foreground">
          Connect your Nightwatch to WiFi
        </p>
      </div>

      {/* Progress bar */}
      {wifi.step !== "complete" && wifi.step !== "error" && (
        <div className="space-y-2">
          <Progress value={getProgress()} className="h-2" />
          <p className="text-xs text-muted-foreground text-center">
            {(wifi.step === "select-network" || wifi.step === "entering-password") &&
              "Step 1: Select your WiFi"}
            {wifi.step === "connecting" && "Step 2: Connecting..."}
          </p>
        </div>
      )}

      {/* Step 1: Select Network */}
      {wifi.step === "select-network" && (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                1
              </span>
              Select Your WiFi
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Choose the WiFi network you want Nightwatch to use.
            </p>
            <NetworkList
              networks={wifi.networks}
              selectedSsid={wifi.selectedSsid}
              onSelect={wifi.setSelectedSsid}
              loading={wifi.networks.length === 0 && !wifi.error}
              error={wifi.error}
              onRetry={wifi.scanWifi}
            />
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={wifi.scanWifi}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 1b: Enter Password */}
      {wifi.step === "entering-password" && (
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-lg">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                  1
                </span>
                Enter Password
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={wifi.goBack}>
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">Selected network</p>
              <p className="font-medium">{wifi.selectedSsid}</p>
            </div>

            <PasswordInput
              value={wifi.password}
              onChange={wifi.setPassword}
              placeholder="Enter WiFi password"
              error={wifi.error}
            />

            <Button
              className="w-full"
              size="lg"
              onClick={wifi.connect}
              disabled={wifi.password.length < 8}
            >
              Connect
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Connecting */}
      {wifi.step === "connecting" && (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                2
              </span>
              Connecting...
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ConnectionStatus
              state="connecting"
              message={`Connecting to ${wifi.selectedSsid}...`}
            />
            <div className="mt-4 p-3 bg-muted/50 rounded-lg">
              <p className="text-xs text-muted-foreground text-center">
                The device will restart and connect to your WiFi network.
                This page will close automatically.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Complete */}
      {wifi.step === "complete" && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardContent className="pt-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500/20 mb-4">
              <Wifi className="h-6 w-6 text-green-500" />
            </div>
            <h3 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-2">
              WiFi Configured!
            </h3>
            <p className="text-sm text-muted-foreground">
              Nightwatch is connecting to <strong>{wifi.selectedSsid}</strong>.
              This page will close shortly.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {wifi.step === "error" && (
        <Card>
          <CardContent className="pt-6">
            <ConnectionStatus
              state="error"
              message={wifi.error || "Something went wrong"}
            />
            <div className="mt-6 flex gap-3">
              <Button variant="outline" className="flex-1" onClick={wifi.goBack}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
              <Button className="flex-1" onClick={wifi.retry}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
