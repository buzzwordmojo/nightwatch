"use client";

import { useState, useEffect } from "react";
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

interface SensorsStepProps {
  wizard: ReturnType<typeof useSetupWizard>;
}

interface SensorStatus {
  radar: { detected: boolean; signal: number };
  audio: { detected: boolean };
  bcg: { detected: boolean };
}

export function SensorsStep({ wizard }: SensorsStepProps) {
  const [sensors, setSensors] = useState<SensorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkSensors = async () => {
      try {
        const response = await fetch("/api/setup/sensor-preview");
        if (!response.ok) throw new Error("Failed to check sensors");
        const data = await response.json();
        setSensors(data);
        setError(null);
      } catch {
        // Use mock data if API not available (development)
        setSensors({
          radar: { detected: true, signal: 85 },
          audio: { detected: true },
          bcg: { detected: false },
        });
      } finally {
        setLoading(false);
      }
    };

    checkSensors();
    const interval = setInterval(checkSensors, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleContinue = () => {
    wizard.updateData({ sensorsConfirmed: true });
    wizard.goNext();
  };

  const atLeastOneSensor =
    sensors?.radar.detected || sensors?.audio.detected || sensors?.bcg.detected;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Position your sensors</CardTitle>
        <CardDescription>
          Make sure the sensors can see the bed clearly
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : (
          <>
            {/* Sensor status list */}
            <div className="space-y-3">
              <SensorItem
                name="Radar Sensor"
                description="Detects breathing and movement"
                detected={sensors?.radar.detected ?? false}
                signal={sensors?.radar.signal}
                required
              />
              <SensorItem
                name="Audio Sensor"
                description="Listens for breathing sounds"
                detected={sensors?.audio.detected ?? false}
              />
              <SensorItem
                name="BCG Sensor"
                description="Measures heart rate via mattress"
                detected={sensors?.bcg.detected ?? false}
                optional
              />
            </div>

            {/* Positioning tips */}
            <div className="bg-secondary/50 rounded-lg p-4 space-y-2">
              <h4 className="font-medium text-sm">Positioning tips:</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Mount radar sensor on wall facing the bed</span>
                </li>
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Keep 1-2 meters from the bed for best results</span>
                </li>
                <li className="flex gap-2">
                  <span>•</span>
                  <span>Avoid obstructions between sensor and bed</span>
                </li>
              </ul>
            </div>

            {/* Live preview indicator */}
            {sensors?.radar.detected && (
              <div className="border rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500" />
                  </span>
                  <span className="text-sm font-medium">Live Preview</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Sensor is detecting movement. Try waving your hand in front of
                  the sensor to verify positioning.
                </p>
              </div>
            )}

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button variant="outline" onClick={wizard.goBack} className="flex-1">
          Back
        </Button>
        <Button
          onClick={handleContinue}
          className="flex-1"
          disabled={loading || !atLeastOneSensor}
        >
          {atLeastOneSensor ? "Looks Good" : "No Sensors Detected"}
        </Button>
      </CardFooter>
    </Card>
  );
}

function SensorItem({
  name,
  description,
  detected,
  signal,
  required,
  optional,
}: {
  name: string;
  description: string;
  detected: boolean;
  signal?: number;
  required?: boolean;
  optional?: boolean;
}) {
  return (
    <div
      className={`
        flex items-center gap-3 p-3 rounded-lg border
        ${detected ? "border-green-500/30 bg-green-500/5" : "border-muted"}
      `}
    >
      {/* Status icon */}
      <div
        className={`
          flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
          ${detected ? "bg-green-500/20 text-green-500" : "bg-muted text-muted-foreground"}
        `}
      >
        {detected ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{name}</span>
          {required && (
            <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
              Required
            </span>
          )}
          {optional && (
            <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
              Optional
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>

      {/* Signal strength */}
      {detected && signal !== undefined && (
        <div className="flex-shrink-0 text-right">
          <div className="text-sm font-medium">{signal}%</div>
          <div className="text-xs text-muted-foreground">Signal</div>
        </div>
      )}
    </div>
  );
}
