"use client";

// Live phase waveforms from the LD6002 vitals radar.
//
// This is the realtime half of the vitals view. It speaks to /ws/waveform on
// the same origin - a raw WebSocket, NOT Convex - because 50 Hz samples are
// deliberately never persisted: sustained writes at that rate are what
// destroyed this device's previous SD card. Closing the view discards the
// trace; the historical view (VitalsChart) reads the 1 Hz rates that ARE
// stored.

import { useEffect, useRef, useState } from "react";

const WINDOW_S = 20;
const MAX = WINDOW_S * 50;

interface Trace {
  key: "resp" | "heart" | "total";
  label: string;
  cssVar: string;
}

const TRACES: Trace[] = [
  { key: "resp", label: "Respiratory phase", cssVar: "--success" },
  { key: "heart", label: "Heartbeat phase", cssVar: "--danger" },
  { key: "total", label: "Total phase", cssVar: "--primary" },
];

export function WaveformChart() {
  const buffers = useRef<Record<string, number[]>>({ resp: [], heart: [], total: [] });
  const canvases = useRef<Record<string, HTMLCanvasElement | null>>({});
  const [status, setStatus] = useState<"connecting" | "live" | "unavailable">("connecting");

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closed = false;
    let raf = 0;

    const connect = () => {
      const proto = location.protocol === "https:" ? "wss://" : "ws://";
      ws = new WebSocket(`${proto}${location.host}/ws/waveform`);
      ws.onopen = () => setStatus("live");
      ws.onclose = () => {
        if (!closed) {
          setStatus("connecting");
          setTimeout(connect, 1500);
        }
      };
      ws.onmessage = (ev) => {
        const m = JSON.parse(ev.data);
        if (m.error) {
          setStatus("unavailable");
          ws?.close();
          closed = true;
          return;
        }
        const b = buffers.current;
        for (const s of m.samples ?? []) {
          b.resp.push(s.resp);
          b.heart.push(s.heart);
          b.total.push(s.total);
        }
        for (const k of ["resp", "heart", "total"]) {
          if (b[k].length > MAX) b[k].splice(0, b[k].length - MAX);
        }
      };
    };

    const css = (v: string) =>
      getComputedStyle(document.documentElement).getPropertyValue(v).trim();

    const draw = () => {
      for (const t of TRACES) {
        const cv = canvases.current[t.key];
        if (!cv) continue;
        const dpr = devicePixelRatio || 1;
        const w = cv.clientWidth;
        const h = cv.clientHeight;
        if (cv.width !== w * dpr || cv.height !== h * dpr) {
          cv.width = w * dpr;
          cv.height = h * dpr;
        }
        const g = cv.getContext("2d");
        if (!g) continue;
        g.setTransform(dpr, 0, 0, dpr, 0, 0);
        g.clearRect(0, 0, w, h);

        g.strokeStyle = `hsl(${css("--border")})`;
        g.lineWidth = 1;
        g.beginPath();
        g.moveTo(0, h / 2);
        g.lineTo(w, h / 2);
        g.stroke();

        const d = buffers.current[t.key];
        if (d.length < 2) continue;
        // Autoscale per window: phase amplitude varies hugely with posture,
        // and a fixed scale flattens the trace to a line most of the time.
        let lo = Infinity;
        let hi = -Infinity;
        for (const v of d) {
          if (v < lo) lo = v;
          if (v > hi) hi = v;
        }
        const pad = (hi - lo) * 0.15 || 0.5;
        lo -= pad;
        hi += pad;
        const span = hi - lo || 1;

        g.strokeStyle = `hsl(${css(t.cssVar)})`;
        g.lineWidth = 1.5;
        g.lineJoin = "round";
        g.beginPath();
        for (let i = 0; i < d.length; i++) {
          const x = (i / (MAX - 1)) * w;
          const y = h - ((d[i] - lo) / span) * h;
          if (i === 0) g.moveTo(x, y);
          else g.lineTo(x, y);
        }
        g.stroke();
      }
      raf = requestAnimationFrame(draw);
    };

    connect();
    raf = requestAnimationFrame(draw);
    return () => {
      closed = true;
      ws?.close();
      cancelAnimationFrame(raf);
    };
  }, []);

  if (status === "unavailable") {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Live waveforms need the LD6002 vitals radar
        (config: detectors.radar.model = ld6002).
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {TRACES.map((t) => (
        <div key={t.key}>
          <h3
            className="mb-1 text-xs font-semibold uppercase tracking-wider"
            style={{ color: `hsl(var(${t.cssVar}))` }}
          >
            {t.label}
          </h3>
          <canvas
            ref={(el) => {
              canvases.current[t.key] = el;
            }}
            className="block h-[110px] w-full"
          />
        </div>
      ))}
      <p className="text-xs text-muted-foreground">
        {status === "live" ? "Streaming at 50 Hz - " : "Connecting - "}
        this trace is never stored; the historical view reads the persisted rates.
      </p>
    </div>
  );
}
