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

interface NameStepProps {
  wizard: ReturnType<typeof useSetupWizard>;
}

const SUGGESTED_NAMES = [
  "Kids Room",
  "Bedroom",
  "Nursery",
  "Guest Room",
];

export function NameStep({ wizard }: NameStepProps) {
  const [name, setName] = useState(wizard.data.monitorName);
  const [touched, setTouched] = useState(false);

  const isValid = name.trim().length >= 2;
  const showError = touched && !isValid;

  const handleContinue = () => {
    setTouched(true);
    if (isValid) {
      wizard.updateData({ monitorName: name.trim() });
      wizard.goNext();
    }
  };

  const handleSuggestion = (suggestion: string) => {
    setName(suggestion);
    setTouched(true);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Name your monitor</CardTitle>
        <CardDescription>
          Give this Nightwatch a name to help identify it
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="monitor-name" className="text-sm font-medium">
            Monitor name
          </label>
          <input
            id="monitor-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => setTouched(true)}
            placeholder="e.g., Kids Room"
            className={`
              w-full px-3 py-2 rounded-md border bg-background
              focus:outline-none focus:ring-2 focus:ring-primary
              ${showError ? "border-destructive" : "border-input"}
            `}
            aria-invalid={showError}
            aria-describedby={showError ? "name-error" : undefined}
            autoFocus
          />
          {showError && (
            <p id="name-error" className="text-sm text-destructive">
              Please enter a name (at least 2 characters)
            </p>
          )}
        </div>

        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_NAMES.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => handleSuggestion(suggestion)}
                className={`
                  px-3 py-1 text-sm rounded-full border transition-colors
                  ${
                    name === suggestion
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-secondary hover:bg-secondary/80 border-transparent"
                  }
                `}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
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
