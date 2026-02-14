"use client";

import { useState } from "react";
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

interface NotificationsStepProps {
  wizard: ReturnType<typeof useSetupWizard>;
}

export function NotificationsStep({ wizard }: NotificationsStepProps) {
  const [audioAlarm, setAudioAlarm] = useState(
    wizard.data.notifications.audioAlarm
  );
  const [pushNotifications, setPushNotifications] = useState(
    wizard.data.notifications.pushNotifications
  );

  const handleContinue = () => {
    wizard.updateData({
      notifications: {
        audioAlarm,
        pushNotifications,
      },
    });
    wizard.goNext();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notification preferences</CardTitle>
        <CardDescription>
          Choose how you want to be alerted
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Audio alarm toggle */}
        <ToggleOption
          title="Audio alarm"
          description="Play a loud alarm on the device when an alert is triggered"
          checked={audioAlarm}
          onChange={setAudioAlarm}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
              />
            </svg>
          }
          recommended
        />

        {/* Push notifications toggle */}
        <ToggleOption
          title="Push notifications"
          description="Send alerts to your phone (requires additional setup)"
          checked={pushNotifications}
          onChange={setPushNotifications}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          }
        />

        {/* Warning if no notifications selected */}
        {!audioAlarm && !pushNotifications && (
          <div className="bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 px-4 py-3 rounded-lg">
            <div className="flex gap-2">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div>
                <p className="font-medium text-sm">No notifications enabled</p>
                <p className="text-sm opacity-80">
                  You won&apos;t be alerted if something needs attention.
                  Consider enabling at least one notification method.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Info about push notifications */}
        {pushNotifications && (
          <div className="bg-secondary/50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground">
              Push notifications will be configured after setup completes.
              You&apos;ll need a Pushover or Ntfy account.
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button variant="outline" onClick={wizard.goBack} className="flex-1">
          Back
        </Button>
        <Button onClick={handleContinue} className="flex-1">
          Continue
        </Button>
      </CardFooter>
    </Card>
  );
}

function ToggleOption({
  title,
  description,
  checked,
  onChange,
  icon,
  recommended,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon: React.ReactNode;
  recommended?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`
        w-full flex items-start gap-3 p-4 rounded-lg border text-left transition-colors
        ${checked
          ? "border-primary bg-primary/5"
          : "border-muted hover:border-muted-foreground/30"
        }
      `}
      role="switch"
      aria-checked={checked}
    >
      {/* Icon */}
      <div
        className={`
          flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
          ${checked ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}
        `}
      >
        {icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium">{title}</span>
          {recommended && (
            <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
              Recommended
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>

      {/* Toggle indicator */}
      <div
        className={`
          flex-shrink-0 w-11 h-6 rounded-full transition-colors relative
          ${checked ? "bg-primary" : "bg-muted"}
        `}
      >
        <div
          className={`
            absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform
            ${checked ? "translate-x-5" : "translate-x-0.5"}
          `}
        />
      </div>
    </button>
  );
}
