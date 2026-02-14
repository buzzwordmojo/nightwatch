"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { useSetupWizard } from "./useSetupWizard";

interface CompleteStepProps {
  wizard: ReturnType<typeof useSetupWizard>;
}

export function CompleteStep({ wizard }: CompleteStepProps) {
  return (
    <Card>
      <CardHeader className="text-center">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-green-500/10 flex items-center justify-center">
          <svg
            className="w-10 h-10 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <CardTitle className="text-green-600 dark:text-green-400">
          Setup Complete!
        </CardTitle>
        <CardDescription>
          {wizard.data.monitorName} is now ready to monitor
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary */}
        <div className="bg-secondary/50 rounded-lg p-4 space-y-3">
          <h4 className="font-medium text-sm">Configuration summary:</h4>
          <div className="space-y-2 text-sm">
            <SummaryItem label="Monitor name" value={wizard.data.monitorName} />
            <SummaryItem
              label="Sensors"
              value={wizard.data.sensorsConfirmed ? "Configured" : "Pending"}
            />
            <SummaryItem
              label="Audio alarm"
              value={wizard.data.notifications.audioAlarm ? "Enabled" : "Disabled"}
            />
            <SummaryItem
              label="Push notifications"
              value={
                wizard.data.notifications.pushNotifications
                  ? "Enabled"
                  : "Disabled"
              }
            />
          </div>
        </div>

        {/* Next steps */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm">Next steps:</h4>
          <div className="grid gap-2">
            <NextStepItem
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              }
              title="Monitor the dashboard"
              description="View real-time vitals and alerts"
            />
            <NextStepItem
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              }
              title="Adjust settings"
              description="Fine-tune alert thresholds and notifications"
            />
            {wizard.data.notifications.pushNotifications && (
              <NextStepItem
                icon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>
                }
                title="Set up push notifications"
                description="Configure Pushover or Ntfy for mobile alerts"
              />
            )}
          </div>
        </div>
      </CardContent>

      <CardFooter>
        <Button asChild className="w-full" size="lg">
          <Link href="/">Go to Dashboard</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function NextStepItem({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-3 items-start">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
        {icon}
      </div>
      <div>
        <p className="font-medium text-sm">{title}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
