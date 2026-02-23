"use client";

import { ShieldCheck, ExternalLink, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface TrustCertCardProps {
  /** URL to open for certificate trust (default: https://192.168.4.1) */
  certUrl?: string;
  /** Called when user clicks "I've accepted, continue" */
  onContinue: () => void;
}

export function TrustCertCard({
  certUrl = "https://192.168.4.1",
  onContinue,
}: TrustCertCardProps) {
  const handleOpenCertPage = () => {
    window.open(certUrl, "_blank");
  };

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary text-sm font-bold">
            <ShieldCheck className="h-4 w-4" />
          </span>
          Trust Security Certificate
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Explanation */}
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground">
            Nightwatch uses a self-signed security certificate. You need to trust it
            once so your phone can find the device on your network.
          </p>
        </div>

        {/* Step 1: Open certificate page */}
        <div className="space-y-3">
          <p className="text-sm font-medium">Step 1: Open this link</p>
          <Button
            variant="outline"
            className="w-full justify-between"
            onClick={handleOpenCertPage}
          >
            <span className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" />
              Open Certificate Page
            </span>
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>

        {/* Step 2: Accept the warning */}
        <div className="space-y-3">
          <p className="text-sm font-medium">Step 2: Accept the certificate</p>
          <div className="text-sm text-muted-foreground space-y-2 pl-4 border-l-2 border-muted">
            <p>When you see a security warning:</p>
            <div className="flex items-center gap-2">
              <ChevronRight className="h-3 w-3" />
              <span>Tap <strong>&quot;Advanced&quot;</strong> or <strong>&quot;Show Details&quot;</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <ChevronRight className="h-3 w-3" />
              <span>Tap <strong>&quot;Proceed&quot;</strong> or <strong>&quot;Visit Site&quot;</strong></span>
            </div>
            <p className="text-xs pt-1 text-muted-foreground/70">
              You should see the Nightwatch dashboard. You can close that tab.
            </p>
          </div>
        </div>

        {/* Continue button */}
        <div className="pt-2 border-t border-border">
          <Button className="w-full" size="lg" onClick={onContinue}>
            I&apos;ve Accepted — Continue Setup
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
