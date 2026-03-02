"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface VitalsData {
  timestamp: number;
  heartRate: number | null;
  respirationRate: number | null;
  movement: number;
  presence: boolean;
  alertLevel: string;
  activeAlerts: any[];
  detectorStatus: Record<string, any>;
  detectors?: Record<string, any>;
}

interface UseNightwatchDataReturn {
  vitals: VitalsData | undefined;
  readings: any[];
  activeAlerts: any[];
  pauseStatus: { paused: boolean; remainingMinutes?: number } | undefined;
  systemHealth: { overall: string } | undefined;
  isConnected: boolean;
}

export function useNightwatchData(): UseNightwatchDataReturn {
  const [vitals, setVitals] = useState<VitalsData | undefined>(undefined);
  const [readings, setReadings] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log("WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Skip ping messages
          if (data.type === "ping") return;

          // Transform Python backend data to match expected format
          const transformed: VitalsData = {
            timestamp: data.timestamp || Date.now() / 1000,
            heartRate: data.heart_rate,
            respirationRate: data.respiration_rate,
            movement: data.movement || 0,
            presence: data.presence || false,
            alertLevel: data.alert_level || "ok",
            activeAlerts: data.active_alerts || [],
            detectorStatus: data.detector_status || {},
            detectors: data.detectors,
          };

          setVitals(transformed);

          // Append to readings for chart
          if (transformed.heartRate !== null || transformed.respirationRate !== null) {
            setReadings((prev) => {
              const newReading = {
                timestamp: transformed.timestamp,
                heartRate: transformed.heartRate,
                respirationRate: transformed.respirationRate,
                movement: transformed.movement,
              };
              // Keep last 480 minutes worth (at 1 reading/sec = 28800)
              const maxReadings = 28800;
              const updated = [...prev, newReading];
              return updated.length > maxReadings
                ? updated.slice(-maxReadings)
                : updated;
            });
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log("WebSocket disconnected, reconnecting in 3s...");
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        ws.close();
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  // Derive pause status and system health from vitals
  const pauseStatus = vitals
    ? {
        paused: (vitals as any).paused || false,
        remainingMinutes: (vitals as any).pause_remaining_minutes,
      }
    : undefined;

  const systemHealth = vitals
    ? {
        overall: vitals.alertLevel === "ok" ? "healthy" : vitals.alertLevel,
      }
    : undefined;

  return {
    vitals,
    readings,
    activeAlerts: vitals?.activeAlerts || [],
    pauseStatus,
    systemHealth,
    isConnected,
  };
}
