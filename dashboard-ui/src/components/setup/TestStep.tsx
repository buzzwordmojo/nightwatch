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

interface TestStepProps {
  wizard: ReturnType<typeof useSetupWizard>;
}

type TestState = "idle" | "testing" | "success" | "failed";

export function TestStep({ wizard }: TestStepProps) {
  const [testState, setTestState] = useState<TestState>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleTest = async () => {
    setTestState("testing");
    setError(null);

    try {
      const response = await fetch("/api/setup/test-alert", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Test failed");
      }

      setTestState("success");
      wizard.updateData({ testCompleted: true });
    } catch {
      setTestState("failed");
      setError("Could not trigger test alert. Please try again.");
    }
  };

  const handleSkip = () => {
    wizard.updateData({ testCompleted: false });
    wizard.goNext();
  };

  const handleContinue = () => {
    wizard.submitSetup();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Test your setup</CardTitle>
        <CardDescription>
          Let&apos;s make sure everything is working correctly
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Test button and status */}
        <div className="text-center py-6 space-y-4">
          {testState === "idle" && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                <svg
                  className="w-10 h-10 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              </div>
              <div>
                <p className="font-medium">Ready to test</p>
                <p className="text-sm text-muted-foreground">
                  This will trigger a brief test alert
                </p>
              </div>
              <Button onClick={handleTest} size="lg">
                Send Test Alert
              </Button>
            </>
          )}

          {testState === "testing" && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
              </div>
              <div>
                <p className="font-medium">Testing...</p>
                <p className="text-sm text-muted-foreground">
                  Sending test alert
                </p>
              </div>
            </>
          )}

          {testState === "success" && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-green-500/10 flex items-center justify-center">
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
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div>
                <p className="font-medium text-green-600 dark:text-green-400">
                  Test successful!
                </p>
                <p className="text-sm text-muted-foreground">
                  Your Nightwatch is ready to use
                </p>
              </div>
            </>
          )}

          {testState === "failed" && (
            <>
              <div className="w-20 h-20 mx-auto rounded-full bg-destructive/10 flex items-center justify-center">
                <svg
                  className="w-10 h-10 text-destructive"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <div>
                <p className="font-medium text-destructive">Test failed</p>
                <p className="text-sm text-muted-foreground">
                  {error || "Something went wrong"}
                </p>
              </div>
              <Button onClick={handleTest} variant="outline">
                Try Again
              </Button>
            </>
          )}
        </div>

        {/* What to expect */}
        <div className="bg-secondary/50 rounded-lg p-4 space-y-2">
          <h4 className="font-medium text-sm">What to expect:</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            {wizard.data.notifications.audioAlarm && (
              <li className="flex gap-2">
                <span>•</span>
                <span>A brief alarm sound will play</span>
              </li>
            )}
            {wizard.data.notifications.pushNotifications && (
              <li className="flex gap-2">
                <span>•</span>
                <span>A test notification will be sent to your phone</span>
              </li>
            )}
            <li className="flex gap-2">
              <span>•</span>
              <span>The dashboard will show a test alert</span>
            </li>
          </ul>
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button variant="outline" onClick={wizard.goBack} className="flex-1">
          Back
        </Button>
        {testState === "success" ? (
          <Button
            onClick={handleContinue}
            className="flex-1"
            disabled={wizard.isSubmitting}
          >
            {wizard.isSubmitting ? "Finishing..." : "Complete Setup"}
          </Button>
        ) : (
          <Button variant="ghost" onClick={handleSkip} className="flex-1">
            Skip for Now
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
