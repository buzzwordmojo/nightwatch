"use client";

import { CheckCircle2, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface WifiSuccessCardProps {
  dashboardUrl: string;
  ssid?: string;
}

export function WifiSuccessCard({ dashboardUrl, ssid }: WifiSuccessCardProps) {
  return (
    <Card variant="success">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <CheckCircle2 className="h-6 w-6 text-success" />
          Nightwatch is Ready!
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-muted-foreground">
          {ssid ? (
            <>
              Your Nightwatch device is now connected to{" "}
              <span className="font-medium text-foreground">{ssid}</span> and ready
              to use.
            </>
          ) : (
            <>Your Nightwatch device is connected and ready to use.</>
          )}
        </p>

        <div className="space-y-3">
          <Button
            asChild
            className="w-full"
            size="lg"
          >
            <a href={dashboardUrl} target="_blank" rel="noopener noreferrer">
              Open Dashboard
              <ExternalLink className="ml-2 h-4 w-4" />
            </a>
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            Bookmark the dashboard for quick access
          </p>
        </div>

        <div className="pt-4 border-t border-border">
          <h4 className="text-sm font-medium mb-2">Next Steps</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Position sensors in the bedroom
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Configure alert preferences
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              Set up push notifications (optional)
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
