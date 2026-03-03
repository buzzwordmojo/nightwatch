"use client";

import { useState, useRef, useCallback, useEffect } from "react";

const SAMPLE_RATE = 16000;

interface UseAudioMonitorReturn {
  isListening: boolean;
  toggle: () => void;
  volume: number;
  setVolume: (v: number) => void;
}

export function useAudioMonitor(): UseAudioMonitorReturn {
  const [isListening, setIsListening] = useState(false);
  const [volume, setVolume] = useState(0.8);

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const nextPlayTimeRef = useRef(0);

  // Update gain node when volume changes
  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = volume;
    }
  }, [volume]);

  const stop = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    gainNodeRef.current = null;
    nextPlayTimeRef.current = 0;
    setIsListening(false);
  }, []);

  const start = useCallback(() => {
    // AudioContext must be created from a user gesture
    const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
    audioCtxRef.current = audioCtx;

    const gainNode = audioCtx.createGain();
    gainNode.gain.value = volume;
    gainNode.connect(audioCtx.destination);
    gainNodeRef.current = gainNode;

    nextPlayTimeRef.current = 0;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/audio`);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setIsListening(true);
    };

    ws.onmessage = (event: MessageEvent) => {
      const ctx = audioCtxRef.current;
      const gain = gainNodeRef.current;
      if (!ctx || !gain || ctx.state === "closed") return;

      const floats = new Float32Array(event.data as ArrayBuffer);
      const buffer = ctx.createBuffer(1, floats.length, SAMPLE_RATE);
      buffer.getChannelData(0).set(floats);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(gain);

      // Schedule playback to avoid gaps
      const now = ctx.currentTime;
      if (nextPlayTimeRef.current < now) {
        nextPlayTimeRef.current = now;
      }
      source.start(nextPlayTimeRef.current);
      nextPlayTimeRef.current += buffer.duration;
    };

    ws.onclose = () => {
      stop();
    };

    ws.onerror = () => {
      stop();
    };
  }, [volume, stop]);

  const toggle = useCallback(() => {
    if (isListening) {
      stop();
    } else {
      start();
    }
  }, [isListening, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
    };
  }, []);

  return { isListening, toggle, volume, setVolume };
}
