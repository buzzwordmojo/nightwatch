"use client";

import { Wifi, Smartphone, Settings, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface HotspotInstructionsProps {
  ssid: string;
  isConnected?: boolean;
  isChecking?: boolean;
  attemptCount?: number;
  /** Called when user manually says they're connected */
  onManualProceed?: () => void;
  /** Called when user completed setup via captive portal popup */
  onSkipToSearch?: () => void;
}

export function HotspotInstructions({
  ssid,
  isConnected,
  isChecking,
  attemptCount = 0,
  onManualProceed,
  onSkipToSearch,
}: HotspotInstructionsProps) {
  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
            1
          </span>
          Connect to Nightwatch
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* SSID Display */}
        <div className="bg-muted/50 rounded-lg p-4 text-center">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
            WiFi Network Name
          </p>
          <p className="text-xl font-mono font-bold text-primary">{ssid}</p>
        </div>

        {/* Instructions */}
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-muted flex items-center justify-center">
              <Settings className="h-3 w-3" />
            </div>
            <p className="text-sm text-muted-foreground">
              Open your phone&apos;s <span className="text-foreground font-medium">Settings</span> app
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-muted flex items-center justify-center">
              <Wifi className="h-3 w-3" />
            </div>
            <p className="text-sm text-muted-foreground">
              Go to <span className="text-foreground font-medium">WiFi</span> settings
            </p>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-muted flex items-center justify-center">
              <Smartphone className="h-3 w-3" />
            </div>
            <p className="text-sm text-muted-foreground">
              Select <span className="text-foreground font-medium">{ssid}</span> and connect
            </p>
          </div>
        </div>

        {/* Status */}
        <div className="pt-2 border-t border-border">
          {isConnected ? (
            <div className="flex items-center justify-center gap-2 text-success">
              <div className="w-2 h-2 rounded-full bg-success" />
              <span className="text-sm font-medium">Connected to Nightwatch!</span>
            </div>
          ) : isChecking ? (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-sm">
                Waiting for connection...
                {attemptCount > 1 && ` (${attemptCount})`}
              </span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-muted" />
              <span className="text-sm">Not connected</span>
            </div>
          )}
        </div>

        {/* Manual options */}
        {(onManualProceed || onSkipToSearch) && (
          <div className="pt-4 space-y-2">
            {onManualProceed && (
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={onManualProceed}
              >
                I&apos;m connected — Continue
              </Button>
            )}
            {onSkipToSearch && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-muted-foreground"
                onClick={onSkipToSearch}
              >
                <Search className="h-4 w-4 mr-2" />
                Already set up WiFi? Find device
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
