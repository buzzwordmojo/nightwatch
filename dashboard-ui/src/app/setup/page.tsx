"use client";

import { useSetupWizard } from "@/components/setup/useSetupWizard";
import { Progress } from "@/components/ui/progress";
import { WelcomeStep } from "@/components/setup/WelcomeStep";
import { NameStep } from "@/components/setup/NameStep";
import { SensorsStep } from "@/components/setup/SensorsStep";
import { NotificationsStep } from "@/components/setup/NotificationsStep";
import { TestStep } from "@/components/setup/TestStep";
import { CompleteStep } from "@/components/setup/CompleteStep";

export default function SetupPage() {
  const wizard = useSetupWizard();

  return (
    <div className="space-y-6">
      {/* Progress bar */}
      {wizard.currentStep !== "complete" && (
        <div className="space-y-2">
          <Progress value={wizard.progress} className="h-2" />
          <p className="text-xs text-muted-foreground text-center">
            Step {wizard.currentIndex + 1} of {wizard.totalSteps}
          </p>
        </div>
      )}

      {/* Error message */}
      {wizard.error && (
        <div
          className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg"
          role="alert"
        >
          <p className="text-sm">{wizard.error}</p>
        </div>
      )}

      {/* Step content */}
      {wizard.currentStep === "welcome" && <WelcomeStep wizard={wizard} />}
      {wizard.currentStep === "name" && <NameStep wizard={wizard} />}
      {wizard.currentStep === "sensors" && <SensorsStep wizard={wizard} />}
      {wizard.currentStep === "notifications" && (
        <NotificationsStep wizard={wizard} />
      )}
      {wizard.currentStep === "test" && <TestStep wizard={wizard} />}
      {wizard.currentStep === "complete" && <CompleteStep wizard={wizard} />}
    </div>
  );
}
