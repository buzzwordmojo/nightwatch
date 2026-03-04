"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Mic, Volume2, Activity, Radio, RefreshCw, AudioWaveform } from "lucide-react";

export default function AudioSettingsPage() {
  const audioSettings = useQuery(api.settings.getAudioSettings);
  const setAudioSettings = useMutation(api.settings.setAudioSettings);
  const vitals = useQuery(api.vitals.getCurrentVitals);

  const [gain, setGain] = useState(50);
  const [breathingThreshold, setBreathingThreshold] = useState(0.005);
  const [silenceThreshold, setSilenceThreshold] = useState(0.001);
  const [freqMin, setFreqMin] = useState(100);
  const [freqMax, setFreqMax] = useState(1200);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  // Noise reduction state
  const [noiseSampling, setNoiseSampling] = useState(false);
  const [noiseStatus, setNoiseStatus] = useState<{
    active: boolean;
    sampling: boolean;
    available: boolean;
  } | null>(null);

  const fetchNoiseStatus = async () => {
    try {
      const res = await fetch("/api/audio/noise-status");
      if (res.ok) setNoiseStatus(await res.json());
    } catch {}
  };

  useEffect(() => {
    fetchNoiseStatus();
  }, []);

  const handleSampleNoise = async () => {
    setNoiseSampling(true);
    try {
      await fetch("/api/audio/sample-noise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration: 5 }),
      });
      await fetchNoiseStatus();
    } catch (e) {
      console.error("Noise sampling failed:", e);
    } finally {
      setNoiseSampling(false);
    }
  };

  const handleClearNoise = async () => {
    try {
      await fetch("/api/audio/clear-noise", { method: "POST" });
      await fetchNoiseStatus();
    } catch (e) {
      console.error("Failed to clear noise profile:", e);
    }
  };

  // Load settings when they arrive
  useEffect(() => {
    if (audioSettings) {
      setGain(audioSettings.gain);
      setBreathingThreshold(audioSettings.breathing_threshold);
      setSilenceThreshold(audioSettings.silence_threshold);
      setFreqMin(audioSettings.breathing_freq_min_hz);
      setFreqMax(audioSettings.breathing_freq_max_hz);
      setDirty(false);
    }
  }, [audioSettings]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await setAudioSettings({
        gain,
        breathing_threshold: breathingThreshold,
        silence_threshold: silenceThreshold,
        breathing_freq_min_hz: freqMin,
        breathing_freq_max_hz: freqMax,
      });
      setDirty(false);
      // Trigger backend to apply settings
      await fetch("/api/audio/apply-settings", { method: "POST" });
    } catch (e) {
      console.error("Failed to save settings:", e);
    } finally {
      setSaving(false);
    }
  };

  const currentLevel = vitals?.detectors?.audio?.value?.breathing_amplitude ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Audio Settings</h2>
        <p className="text-sm text-muted-foreground">
          Adjust microphone sensitivity for breathing detection
        </p>
      </div>

      {/* Live Level Indicator */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium flex items-center gap-2">
              <Mic className="h-4 w-4" />
              Live Audio Level
            </h3>
            <span className="text-2xl font-mono">
              {Math.round(currentLevel * 100)}%
            </span>
          </div>
          <div className="h-4 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full transition-all duration-100"
              style={{
                width: `${Math.min(100, currentLevel * 100)}%`,
                backgroundColor:
                  currentLevel < 0.3
                    ? "#22c55e"
                    : currentLevel < 0.7
                      ? "#eab308"
                      : "#ef4444",
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Speak or breathe near the mic to test sensitivity
          </p>
        </CardContent>
      </Card>

      {/* Background Noise Reduction */}
      {noiseStatus?.available && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium flex items-center gap-2">
                <AudioWaveform className="h-4 w-4" />
                Background Noise Reduction
              </h3>
              {noiseStatus.active && (
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/15 text-green-500">
                  Active
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Sample the room&apos;s background noise to subtract it from live
              audio. Keep the room quiet during sampling — no talking or
              movement.
            </p>
            <div className="flex gap-3">
              <Button
                onClick={handleSampleNoise}
                disabled={noiseSampling}
                variant={noiseStatus.active ? "outline" : "default"}
              >
                {noiseSampling ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sampling...
                  </>
                ) : (
                  noiseStatus.active ? "Re-sample" : "Sample Background Noise"
                )}
              </Button>
              {noiseStatus.active && (
                <Button variant="outline" onClick={handleClearNoise}>
                  Clear Profile
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gain Control */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Volume2 className="h-4 w-4 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Software Gain</h3>
                <p className="text-sm text-muted-foreground">
                  Amplifies the microphone signal
                </p>
              </div>
            </div>
            <span className="text-lg font-mono w-16 text-right">{gain}x</span>
          </div>
          <Slider
            value={[gain]}
            onValueChange={([v]: number[]) => {
              setGain(v);
              setDirty(true);
            }}
            min={1}
            max={100}
            step={1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>1x (quiet)</span>
            <span>100x (very sensitive)</span>
          </div>
        </CardContent>
      </Card>

      {/* Detection Thresholds */}
      <Card>
        <CardContent className="p-6 space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Breathing Detection Threshold</h3>
                <p className="text-sm text-muted-foreground">
                  Lower = more sensitive to quiet breathing
                </p>
              </div>
              <span className="ml-auto text-lg font-mono">
                {breathingThreshold.toFixed(4)}
              </span>
            </div>
            <Slider
              value={[breathingThreshold * 1000]}
              onValueChange={([v]: number[]) => {
                setBreathingThreshold(v / 1000);
                setDirty(true);
              }}
              min={0.5}
              max={50}
              step={0.5}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0.0005 (very sensitive)</span>
              <span>0.05 (less sensitive)</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-4">
              <Radio className="h-4 w-4 text-muted-foreground" />
              <div>
                <h3 className="font-medium">Silence Threshold</h3>
                <p className="text-sm text-muted-foreground">
                  Lower = quieter sounds count as &quot;not silent&quot;
                </p>
              </div>
              <span className="ml-auto text-lg font-mono">
                {silenceThreshold.toFixed(4)}
              </span>
            </div>
            <Slider
              value={[silenceThreshold * 1000]}
              onValueChange={([v]: number[]) => {
                setSilenceThreshold(v / 1000);
                setDirty(true);
              }}
              min={0.1}
              max={20}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0.0001 (very quiet)</span>
              <span>0.02 (louder)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Frequency Range */}
      <Card>
        <CardContent className="p-6 space-y-6">
          <div>
            <h3 className="font-medium mb-1">Breathing Frequency Range</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Audio frequencies to analyze for breathing sounds (Hz)
            </p>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm">Minimum Frequency</span>
                  <span className="font-mono">{freqMin} Hz</span>
                </div>
                <Slider
                  value={[freqMin]}
                  onValueChange={([v]: number[]) => {
                    setFreqMin(v);
                    setDirty(true);
                  }}
                  min={50}
                  max={500}
                  step={10}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm">Maximum Frequency</span>
                  <span className="font-mono">{freqMax} Hz</span>
                </div>
                <Slider
                  value={[freqMax]}
                  onValueChange={([v]: number[]) => {
                    setFreqMax(v);
                    setDirty(true);
                  }}
                  min={500}
                  max={3000}
                  step={50}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        <Button
          variant="outline"
          disabled={!dirty || saving}
          onClick={() => {
            if (audioSettings) {
              setGain(audioSettings.gain);
              setBreathingThreshold(audioSettings.breathing_threshold);
              setSilenceThreshold(audioSettings.silence_threshold);
              setFreqMin(audioSettings.breathing_freq_min_hz);
              setFreqMax(audioSettings.breathing_freq_max_hz);
              setDirty(false);
            }
          }}
        >
          Reset
        </Button>
        <Button onClick={handleSave} disabled={!dirty || saving}>
          {saving ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Applying...
            </>
          ) : (
            "Save & Apply"
          )}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Changes are applied immediately to the audio detector
      </p>
    </div>
  );
}
