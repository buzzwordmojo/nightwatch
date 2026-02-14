"use client";

import { useState, useCallback } from "react";

export type SetupStep =
  | "welcome"
  | "name"
  | "sensors"
  | "notifications"
  | "test"
  | "complete";

export interface SetupData {
  monitorName: string;
  sensorsConfirmed: boolean;
  notifications: {
    audioAlarm: boolean;
    pushNotifications: boolean;
    pushProvider?: "pushover" | "ntfy";
  };
  testCompleted: boolean;
}

const STEPS: SetupStep[] = [
  "welcome",
  "name",
  "sensors",
  "notifications",
  "test",
  "complete",
];

const initialData: SetupData = {
  monitorName: "",
  sensorsConfirmed: false,
  notifications: {
    audioAlarm: true,
    pushNotifications: false,
  },
  testCompleted: false,
};

export function useSetupWizard() {
  const [currentStep, setCurrentStep] = useState<SetupStep>("welcome");
  const [data, setData] = useState<SetupData>(initialData);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentIndex = STEPS.indexOf(currentStep);
  const totalSteps = STEPS.length;
  const progress = ((currentIndex + 1) / totalSteps) * 100;

  const canGoBack = currentIndex > 0 && currentStep !== "complete";
  const canGoNext = currentIndex < STEPS.length - 1;

  const goNext = useCallback(() => {
    if (canGoNext) {
      setCurrentStep(STEPS[currentIndex + 1]);
      setError(null);
    }
  }, [canGoNext, currentIndex]);

  const goBack = useCallback(() => {
    if (canGoBack) {
      setCurrentStep(STEPS[currentIndex - 1]);
      setError(null);
    }
  }, [canGoBack, currentIndex]);

  const goToStep = useCallback((step: SetupStep) => {
    setCurrentStep(step);
    setError(null);
  }, []);

  const updateData = useCallback((updates: Partial<SetupData>) => {
    setData((prev) => ({ ...prev, ...updates }));
  }, []);

  const submitSetup = useCallback(async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/setup/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Setup failed");
      }

      goNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setIsSubmitting(false);
    }
  }, [data, goNext]);

  return {
    currentStep,
    currentIndex,
    totalSteps,
    progress,
    data,
    isSubmitting,
    error,
    canGoBack,
    canGoNext,
    goNext,
    goBack,
    goToStep,
    updateData,
    submitSetup,
    setError,
  };
}
