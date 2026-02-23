"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  NetworkList,
  PasswordInput,
  ConnectionStatus,
  HotspotInstructions,
  WifiSuccessCard,
  TrustCertCard,
  useWifiSetup,
} from "@/components/wifi";
import { ArrowLeft, RefreshCw, Loader2 } from "lucide-react";

const PORTAL_URL = "http://192.168.4.1";

function ProctorContent() {
  const searchParams = useSearchParams();
  const deviceId = searchParams.get("id") || "Nightwatch";

  const wifi = useWifiSetup({
    portalUrl: PORTAL_URL,
    deviceId,
    autoStart: true,
  });

  // Calculate progress percentage (4 steps now: connect, trust-cert, select-wifi, connect)
  const getProgress = () => {
    switch (wifi.step) {
      case "connect-hotspot":
        return 0;
      case "trust-cert":
        return 25;
      case "select-network":
      case "entering-password":
        return 50;
      case "connecting":
      case "searching":
        return 75;
      case "complete":
        return 100;
      default:
        return 0;
    }
  };

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      {wifi.step !== "complete" && wifi.step !== "error" && (
        <div className="space-y-2">
          <Progress value={getProgress()} className="h-2" />
          <p className="text-xs text-muted-foreground text-center">
            {wifi.step === "connect-hotspot" && "Step 1: Connect to device"}
            {wifi.step === "trust-cert" && "Step 2: Trust certificate"}
            {(wifi.step === "select-network" || wifi.step === "entering-password") &&
              "Step 3: Select your WiFi"}
            {(wifi.step === "connecting" || wifi.step === "searching") &&
              "Step 4: Connecting..."}
          </p>
        </div>
      )}

      {/* Step 1: Connect to Hotspot */}
      {wifi.step === "connect-hotspot" && (
        <HotspotInstructions
          ssid={deviceId}
          isConnected={wifi.hotspotConnected}
          isChecking={true}
          attemptCount={wifi.hotspotAttempts}
        />
      )}

      {/* Step 2: Trust Certificate */}
      {wifi.step === "trust-cert" && (
        <TrustCertCard
          certUrl="https://192.168.4.1"
          onContinue={wifi.proceedAfterCertTrust}
        />
      )}

      {/* Step 3: Select Network */}
      {wifi.step === "select-network" && (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                3
              </span>
              Select Your WiFi
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Choose your home WiFi network to connect Nightwatch to the internet.
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

      {/* Step 3b: Enter Password */}
      {wifi.step === "entering-password" && (
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-lg">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                  3
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

      {/* Step 4: Connecting / Searching */}
      {(wifi.step === "connecting" || wifi.step === "searching") && (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-lg">
              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
                4
              </span>
              {wifi.step === "connecting" ? "Connecting..." : "Finding Nightwatch..."}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ConnectionStatus
              state={wifi.step === "connecting" ? "connecting" : "searching"}
              message={
                wifi.step === "connecting"
                  ? `Connecting to ${wifi.selectedSsid}...`
                  : "Searching for Nightwatch on your network..."
              }
              progress={wifi.searchProgress || undefined}
            />
            <div className="mt-4 p-3 bg-muted/50 rounded-lg">
              <p className="text-xs text-muted-foreground text-center">
                {wifi.step === "connecting"
                  ? "The device will disconnect from the setup hotspot and connect to your WiFi."
                  : "Your phone should automatically reconnect to your home WiFi."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 5: Complete */}
      {wifi.step === "complete" && wifi.dashboardUrl && (
        <WifiSuccessCard
          dashboardUrl={wifi.dashboardUrl}
          ssid={wifi.selectedSsid || undefined}
        />
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

function ProctorLoading() {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

export default function ProctorPage() {
  return (
    <Suspense fallback={<ProctorLoading />}>
      <ProctorContent />
    </Suspense>
  );
}
