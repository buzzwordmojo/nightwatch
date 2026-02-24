"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, Download, Smartphone } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface CertInstallCardProps {
  onContinue: () => void;
}

type Platform = "ios" | "android";

export function CertInstallCard({ onContinue }: CertInstallCardProps) {
  const [platform, setPlatform] = useState<Platform>("ios");

  useEffect(() => {
    // Auto-detect platform
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes("android")) {
      setPlatform("android");
    }
  }, []);

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <ShieldCheck className="h-5 w-5 text-primary" />
          Install Security Certificate
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-muted-foreground">
          Install the Nightwatch certificate for secure, warning-free access to your dashboard.
        </p>

        {/* Platform selector */}
        <div className="flex gap-2">
          <Button
            variant={platform === "ios" ? "default" : "outline"}
            size="sm"
            className="flex-1"
            onClick={() => setPlatform("ios")}
          >
            iPhone
          </Button>
          <Button
            variant={platform === "android" ? "default" : "outline"}
            size="sm"
            className="flex-1"
            onClick={() => setPlatform("android")}
          >
            <Smartphone className="h-4 w-4 mr-1" />
            Android
          </Button>
        </div>

        {/* iOS instructions */}
        {platform === "ios" && (
          <div className="space-y-4">
            <Button asChild className="w-full" size="lg">
              <a href="/api/setup/certificate.mobileconfig">
                <Download className="h-4 w-4 mr-2" />
                Download Profile
              </a>
            </Button>
            <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
              <li>Tap <strong className="text-foreground">Download Profile</strong> above</li>
              <li>Open <strong className="text-foreground">Settings</strong> → <strong className="text-foreground">Profile Downloaded</strong></li>
              <li>Tap <strong className="text-foreground">Install</strong> and enter your passcode</li>
              <li>Go to <strong className="text-foreground">Settings</strong> → <strong className="text-foreground">General</strong> → <strong className="text-foreground">About</strong> → <strong className="text-foreground">Certificate Trust Settings</strong></li>
              <li>Enable trust for <strong className="text-foreground">Nightwatch CA</strong></li>
            </ol>
          </div>
        )}

        {/* Android instructions */}
        {platform === "android" && (
          <div className="space-y-4">
            <Button asChild className="w-full" size="lg">
              <a href="/api/setup/certificate">
                <Download className="h-4 w-4 mr-2" />
                Download Certificate
              </a>
            </Button>
            <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
              <li>Tap <strong className="text-foreground">Download Certificate</strong> above</li>
              <li>Open <strong className="text-foreground">Settings</strong> → <strong className="text-foreground">Security</strong></li>
              <li>Tap <strong className="text-foreground">Encryption & credentials</strong> → <strong className="text-foreground">Install a certificate</strong></li>
              <li>Select <strong className="text-foreground">CA certificate</strong></li>
              <li>Choose the downloaded file and install</li>
            </ol>
            <p className="text-xs text-muted-foreground/70">
              Note: You may need to set a screen lock if you haven&apos;t already.
            </p>
          </div>
        )}

        <div className="pt-4 border-t">
          <Button className="w-full" variant="outline" onClick={onContinue}>
            I&apos;ve Installed the Certificate — Continue
          </Button>
          <p className="text-xs text-muted-foreground text-center mt-2">
            You can also skip this and accept browser warnings later
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
