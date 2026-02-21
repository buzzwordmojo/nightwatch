"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { checkHealth, scanNetworks, submitCredentials, type Network } from "@/lib/wifi-api";
import { pollForDevice } from "@/lib/ip-scanner";

export type WifiSetupStep =
  | "connect-hotspot"
  | "select-network"
  | "entering-password"
  | "connecting"
  | "searching"
  | "complete"
  | "error";

export interface WifiSetupState {
  step: WifiSetupStep;
  networks: Network[];
  selectedSsid: string | null;
  password: string;
  error: string | null;
  dashboardUrl: string | null;
  hotspotConnected: boolean;
  hotspotAttempts: number;
  searchProgress: { current: number; total: number } | null;
}

export interface WifiSetupActions {
  setSelectedSsid: (ssid: string | null) => void;
  setPassword: (password: string) => void;
  scanWifi: () => Promise<void>;
  connect: () => Promise<void>;
  retry: () => void;
  goBack: () => void;
}

export interface UseWifiSetupOptions {
  /** URL of the captive portal (default: http://192.168.4.1) */
  portalUrl?: string;
  /** Device ID for hotspot SSID display */
  deviceId?: string;
  /** Auto-start hotspot detection polling */
  autoStart?: boolean;
  /** Skip hotspot detection (for portal page where we're already on hotspot) */
  skipHotspotDetection?: boolean;
  /** Skip device search after connect (for portal page where browser closes) */
  skipDeviceSearch?: boolean;
}

export function useWifiSetup(options: UseWifiSetupOptions = {}): WifiSetupState & WifiSetupActions {
  const {
    portalUrl = "http://192.168.4.1",
    autoStart = true,
    skipHotspotDetection = false,
    skipDeviceSearch = false,
  } = options;

  const [state, setState] = useState<WifiSetupState>({
    step: skipHotspotDetection ? "select-network" : "connect-hotspot",
    networks: [],
    selectedSsid: null,
    password: "",
    error: null,
    dashboardUrl: null,
    hotspotConnected: false,
    hotspotAttempts: 0,
    searchProgress: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const pollingRef = useRef<number | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  // Poll for hotspot connection
  const checkHotspotConnection = useCallback(async () => {
    setState((s) => ({ ...s, hotspotAttempts: s.hotspotAttempts + 1 }));

    const health = await checkHealth(portalUrl, 2000);

    if (health) {
      setState((s) => ({
        ...s,
        hotspotConnected: true,
        step: "select-network",
      }));
      // Auto-scan networks when hotspot detected
      return true;
    }

    return false;
  }, [portalUrl]);

  // Start hotspot polling (skip if skipHotspotDetection is true)
  useEffect(() => {
    if (!autoStart || skipHotspotDetection || state.step !== "connect-hotspot") return;

    const poll = async () => {
      const connected = await checkHotspotConnection();
      if (!connected && state.step === "connect-hotspot") {
        pollingRef.current = window.setTimeout(poll, 2000);
      }
    };

    poll();

    return () => {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, [autoStart, skipHotspotDetection, state.step, checkHotspotConnection]);

  // Auto-scan when entering select-network step
  useEffect(() => {
    if (state.step === "select-network" && state.networks.length === 0) {
      scanWifi();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.step]);

  const setSelectedSsid = useCallback((ssid: string | null) => {
    setState((s) => ({
      ...s,
      selectedSsid: ssid,
      step: ssid ? "entering-password" : "select-network",
      password: "",
      error: null,
    }));
  }, []);

  const setPassword = useCallback((password: string) => {
    setState((s) => ({ ...s, password, error: null }));
  }, []);

  const scanWifi = useCallback(async () => {
    setState((s) => ({ ...s, error: null }));

    try {
      const networks = await scanNetworks(portalUrl);
      setState((s) => ({ ...s, networks }));
    } catch (error) {
      setState((s) => ({
        ...s,
        error: error instanceof Error ? error.message : "Failed to scan networks",
      }));
    }
  }, [portalUrl]);

  const connect = useCallback(async () => {
    const { selectedSsid, password } = state;

    if (!selectedSsid || password.length < 8) {
      setState((s) => ({
        ...s,
        error: "Please select a network and enter a valid password",
      }));
      return;
    }

    setState((s) => ({ ...s, step: "connecting", error: null }));

    try {
      // Submit credentials
      await submitCredentials(portalUrl, selectedSsid, password);

      // For portal page, skip device search (browser will close)
      if (skipDeviceSearch) {
        // Mark setup as complete
        if (typeof window !== "undefined") {
          localStorage.setItem("nightwatch_setup_complete", "true");
        }
        setState((s) => ({
          ...s,
          step: "complete",
          searchProgress: null,
        }));
        return;
      }

      // Move to searching step
      setState((s) => ({ ...s, step: "searching" }));

      // Create abort controller for search
      abortControllerRef.current = new AbortController();

      // Poll for device on home network
      const result = await pollForDevice({
        maxAttempts: 45,
        intervalMs: 2000,
        signal: abortControllerRef.current.signal,
        onAttempt: (attempt, maxAttempts) => {
          setState((s) => ({
            ...s,
            searchProgress: { current: attempt, total: maxAttempts },
          }));
        },
      });

      if (result.found && result.url) {
        // Mark setup as complete
        if (typeof window !== "undefined") {
          localStorage.setItem("nightwatch_setup_complete", "true");
        }
        setState((s) => ({
          ...s,
          step: "complete",
          dashboardUrl: result.url,
          searchProgress: null,
        }));
      } else {
        setState((s) => ({
          ...s,
          step: "error",
          error: "Could not find Nightwatch on your network. Please try again.",
          searchProgress: null,
        }));
      }
    } catch (error) {
      setState((s) => ({
        ...s,
        step: "error",
        error: error instanceof Error ? error.message : "Connection failed",
        searchProgress: null,
      }));
    }
  }, [state, portalUrl, skipDeviceSearch]);

  const retry = useCallback(() => {
    setState((s) => ({
      ...s,
      step: "select-network",
      error: null,
      password: "",
      searchProgress: null,
    }));
  }, []);

  const goBack = useCallback(() => {
    setState((s) => {
      switch (s.step) {
        case "entering-password":
          return { ...s, step: "select-network", selectedSsid: null, password: "" };
        case "error":
          return { ...s, step: "select-network", error: null };
        default:
          return s;
      }
    });
  }, []);

  return {
    ...state,
    setSelectedSsid,
    setPassword,
    scanWifi,
    connect,
    retry,
    goBack,
  };
}
