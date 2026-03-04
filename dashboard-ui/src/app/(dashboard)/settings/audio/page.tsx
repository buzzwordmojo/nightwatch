"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../../../../../convex/_generated/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Mic, Volume2, VolumeX, Activity, Radio, RefreshCw, AudioWaveform, Wand2, Check, Wind, Timer } from "lucide-react";
import { useAudioMonitor } from "@/hooks/useAudioMonitor";

interface NoiseProfile {
  overall_db: number;
  dominant_freqs: { hz: number; db: number; label: string }[];
  band_energy: { low: number; mid: number; high: number };
  noise_type: string;
}

interface NoiseStatus {
  active: boolean;
  sampling: boolean;
  available: boolean;
  enabled: boolean;
  profile?: NoiseProfile;
}

interface AutoTuneRecommendations {
  gain: number;
  silence_threshold: number;
  breathing_threshold: number;
}

interface AutoTuneResult {
  success: boolean;
  error?: string;
  recommendations?: AutoTuneRecommendations;
  statistics?: Record<string, number>;
  noise_profile_updated?: boolean;
}

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

  // Live listen
  const { isListening, toggle: toggleListen } = useAudioMonitor();

  // Noise reduction state
  const [noiseSampling, setNoiseSampling] = useState(false);
  const [noiseStatus, setNoiseStatus] = useState<NoiseStatus | null>(null);

  // Auto-tune state
  const [tuning, setTuning] = useState(false);
  const [tunePhase, setTunePhase] = useState("");
  const [tuneProgress, setTuneProgress] = useState(0);
  const [tuneResult, setTuneResult] = useState<AutoTuneResult | null>(null);
  const tuneTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Live preview debounce
  const previewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const previewSettings = useCallback((g: number, bt: number, st: number) => {
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    previewTimerRef.current = setTimeout(() => {
      fetch("/api/audio/preview-settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gain: g,
          breathing_threshold: bt,
          silence_threshold: st,
        }),
      }).catch(() => {});
    }, 200);
  }, []);

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

  const handleToggleNoiseEnabled = async () => {
    if (!noiseStatus) return;
    const newEnabled = !noiseStatus.enabled;
    try {
      await fetch("/api/audio/noise-enabled", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: newEnabled }),
      });
      setNoiseStatus((prev) => prev ? { ...prev, enabled: newEnabled } : prev);
    } catch (e) {
      console.error("Failed to toggle noise reduction:", e);
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
      // Settings are already live via preview — persist to YAML without restart
      await fetch("/api/audio/apply-settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ restart: false }),
      });
    } catch (e) {
      console.error("Failed to save settings:", e);
    } finally {
      setSaving(false);
    }
  };

  // Auto-tune
  const handleAutoTune = async () => {
    setTuning(true);
    setTuneResult(null);
    setTuneProgress(0);
    setTunePhase("Sampling noise...");

    // Frontend progress timer (~22s total)
    const startTime = Date.now();
    const totalMs = 22000;
    tuneTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(99, (elapsed / totalMs) * 100);
      setTuneProgress(pct);
      if (elapsed < 5000) {
        setTunePhase("Sampling noise...");
      } else if (elapsed < 20000) {
        setTunePhase("Collecting stats...");
      } else {
        setTunePhase("Calculating...");
      }
    }, 200);

    try {
      const res = await fetch("/api/audio/auto-tune", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const result: AutoTuneResult = await res.json();
      setTuneResult(result);
      setTuneProgress(100);
      setTunePhase(result.success ? "Complete" : "Failed");
    } catch (e) {
      console.error("Auto-tune failed:", e);
      setTuneResult({ success: false, error: "Request failed" });
      setTunePhase("Failed");
    } finally {
      if (tuneTimerRef.current) clearInterval(tuneTimerRef.current);
      setTuning(false);
    }
  };

  const handleApplyRecommendations = () => {
    if (!tuneResult?.recommendations) return;
    const rec = tuneResult.recommendations;
    setGain(rec.gain);
    setBreathingThreshold(rec.breathing_threshold);
    setSilenceThreshold(rec.silence_threshold);
    setDirty(true);
    previewSettings(rec.gain, rec.breathing_threshold, rec.silence_threshold);
    setTuneResult(null);
  };

  const currentLevel = vitals?.detectors?.audio?.value?.breathing_amplitude ?? 0;
  const audioValue = vitals?.detectors?.audio?.value;

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
            <div className="flex items-center gap-3">
              <span className="text-2xl font-mono">
                {Math.round(currentLevel * 100)}%
              </span>
              <Button
                size="sm"
                variant={isListening ? "default" : "outline"}
                onClick={toggleListen}
                className="gap-1.5"
              >
                {isListening ? (
                  <>
                    <Volume2 className="h-3.5 w-3.5 animate-pulse" />
                    <span>Live</span>
                  </>
                ) : (
                  <>
                    <VolumeX className="h-3.5 w-3.5" />
                    <span>Listen</span>
                  </>
                )}
              </Button>
            </div>
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
            {isListening
              ? "Listening — audio is playing through your speakers"
              : "Speak or breathe near the mic to test sensitivity"}
          </p>
        </CardContent>
      </Card>

      {/* Detection Status (real-time) */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-medium flex items-center gap-2 mb-4">
            <Activity className="h-4 w-4" />
            Detection Status
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className={`text-2xl font-mono ${audioValue?.breathing_detected ? "text-green-500" : "text-muted-foreground"}`}>
                {audioValue?.breathing_detected ? (
                  <Wind className="h-6 w-6 mx-auto" />
                ) : (
                  <span className="text-sm">--</span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Breathing</p>
              {audioValue?.breathing_rate && (
                <p className="text-sm font-mono">{audioValue.breathing_rate} bpm</p>
              )}
            </div>
            <div className="text-center">
              <div className="text-2xl font-mono">
                <Timer className={`h-6 w-6 mx-auto ${(audioValue?.silence_duration ?? 0) > 5 ? "text-amber-500" : "text-muted-foreground"}`} />
              </div>
              <p className="text-xs text-muted-foreground mt-1">Silence</p>
              <p className="text-sm font-mono">{audioValue?.silence_duration ?? 0}s</p>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-mono ${audioValue?.vocalization_detected ? "text-amber-500" : "text-muted-foreground"}`}>
                <Mic className={`h-6 w-6 mx-auto ${audioValue?.vocalization_detected ? "text-amber-500" : "text-muted-foreground"}`} />
              </div>
              <p className="text-xs text-muted-foreground mt-1">Vocalization</p>
              <p className="text-sm font-mono">{audioValue?.vocalization_detected ? "Yes" : "No"}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-3 text-center">
            Updates in real-time as you adjust thresholds below
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
                <button
                  onClick={handleToggleNoiseEnabled}
                  className={`text-xs font-medium px-2 py-0.5 rounded-full cursor-pointer transition-colors ${
                    noiseStatus.enabled
                      ? "bg-green-500/15 text-green-500 hover:bg-green-500/25"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {noiseStatus.enabled ? "Active" : "Paused"}
                </button>
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

            {/* Noise Profile Characteristics */}
            {noiseStatus.active && noiseStatus.profile && (
              <div className="mt-5 pt-4 border-t border-border space-y-3">
                <p className="text-sm font-medium">{noiseStatus.profile.noise_type}</p>

                {/* Band Energy Bar */}
                <div>
                  <p className="text-xs text-muted-foreground mb-1.5">Frequency distribution</p>
                  <div className="flex h-3 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-500"
                      style={{ width: `${noiseStatus.profile.band_energy.low}%` }}
                      title={`Low: ${noiseStatus.profile.band_energy.low}%`}
                    />
                    <div
                      className="bg-amber-500"
                      style={{ width: `${noiseStatus.profile.band_energy.mid}%` }}
                      title={`Mid: ${noiseStatus.profile.band_energy.mid}%`}
                    />
                    <div
                      className="bg-rose-500"
                      style={{ width: `${noiseStatus.profile.band_energy.high}%` }}
                      title={`High: ${noiseStatus.profile.band_energy.high}%`}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                    <span>Low &lt;500 Hz ({noiseStatus.profile.band_energy.low}%)</span>
                    <span>Mid ({noiseStatus.profile.band_energy.mid}%)</span>
                    <span>High 2k+ Hz ({noiseStatus.profile.band_energy.high}%)</span>
                  </div>
                </div>

                {/* Dominant Frequencies */}
                {noiseStatus.profile.dominant_freqs.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {noiseStatus.profile.dominant_freqs.map((f, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
                        title={f.label}
                      >
                        {Math.round(f.hz)} Hz
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
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
              previewSettings(v, breathingThreshold, silenceThreshold);
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
                const bt = v / 1000;
                setBreathingThreshold(bt);
                setDirty(true);
                previewSettings(gain, bt, silenceThreshold);
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
                const st = v / 1000;
                setSilenceThreshold(st);
                setDirty(true);
                previewSettings(gain, breathingThreshold, st);
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

      {/* Auto-Tune */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium flex items-center gap-2">
              <Wand2 className="h-4 w-4" />
              Auto-Tune
            </h3>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Automatically calibrate gain and detection thresholds based on your
            room&apos;s ambient noise. Takes about 22 seconds.
          </p>

          {/* Progress bar during tuning */}
          {(tuning || tuneProgress > 0) && !tuneResult && (
            <div className="mb-4">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>{tunePhase}</span>
                <span>{Math.round(tuneProgress)}%</span>
              </div>
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-200 rounded-full"
                  style={{ width: `${tuneProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Results */}
          {tuneResult && tuneResult.success && tuneResult.recommendations && (
            <div className="mb-4 p-4 bg-secondary/50 rounded-lg space-y-3">
              <p className="text-sm font-medium flex items-center gap-1.5">
                <Check className="h-4 w-4 text-green-500" />
                Recommended Settings
              </p>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-xs text-muted-foreground">Gain</p>
                  <p className="text-lg font-mono">{tuneResult.recommendations.gain}x</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Breathing</p>
                  <p className="text-lg font-mono">{tuneResult.recommendations.breathing_threshold.toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Silence</p>
                  <p className="text-lg font-mono">{tuneResult.recommendations.silence_threshold.toFixed(4)}</p>
                </div>
              </div>
              <Button onClick={handleApplyRecommendations} className="w-full">
                Apply Recommendations
              </Button>
            </div>
          )}

          {tuneResult && !tuneResult.success && (
            <div className="mb-4 p-3 bg-destructive/10 text-destructive text-sm rounded-lg">
              Auto-tune failed: {tuneResult.error ?? "Unknown error"}
            </div>
          )}

          <Button
            onClick={handleAutoTune}
            disabled={tuning}
            variant="outline"
            className="w-full"
          >
            {tuning ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Tuning...
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4 mr-2" />
                Start Auto-Tune
              </>
            )}
          </Button>
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
              // Revert runtime to saved values
              previewSettings(
                audioSettings.gain,
                audioSettings.breathing_threshold,
                audioSettings.silence_threshold,
              );
            }
          }}
        >
          Reset
        </Button>
        <Button onClick={handleSave} disabled={!dirty || saving}>
          {saving ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            "Save"
          )}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Slider changes preview instantly — Save persists to config
      </p>
    </div>
  );
}
