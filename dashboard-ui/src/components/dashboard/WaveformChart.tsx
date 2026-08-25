"use client";

// Live phase waveforms from the LD6002 vitals radar.
//
// Speaks to /ws/waveform on the same origin - a raw WebSocket, NOT Convex -
// because 50 Hz samples are deliberately never persisted. Two properties are
// load-bearing here:
//
// 1. The x-axis is time, not sample count. With an empty room the module
//    stops producing phase frames entirely, so a count-based window freezes
//    on its last trace and presents stale data as current. A time-based
//    window slides on regardless, and the trace visibly drains away.
// 2. The server heartbeats once a second even with zero samples, carrying
//    presence - so the client can tell "room is empty" (show it honestly)
//    from "connection died" (reconnect).

import { useEffect, useRef, useState } from "react";

const WINDOW_S = 20;

interface Sample {
  t: number;
  v: number;
}

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
  const buffers = useRef<Record<string, Sample[]>>({ resp: [], heart: [], total: [] });
  // Server clock anchor: serverNow at wall time anchorWall. Advancing it by
  // the local clock keeps the window sliding between (and without) messages.
  const clock = useRef<{ serverNow: number; anchorWall: number }>({ serverNow: 0, anchorWall: 0 });
  const canvases = useRef<Record<string, HTMLCanvasElement | null>>({});
  const [status, setStatus] = useState<"connecting" | "live" | "unavailable">("connecting");
  const [present, setPresent] = useState<boolean | null>(null);

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
          closed = true;
          ws?.close();
          return;
        }
        if (typeof m.now === "number") {
          clock.current = { serverNow: m.now, anchorWall: performance.now() };
        }
        if (m.vitals && typeof m.vitals.presence === "boolean") {
          setPresent(m.vitals.presence);
        }
        const b = buffers.current;
        for (const s of m.samples ?? []) {
          b.resp.push({ t: s.t, v: s.resp });
          b.heart.push({ t: s.t, v: s.heart });
          b.total.push({ t: s.t, v: s.total });
        }
      };
    };

    const css = (v: string) =>
      getComputedStyle(document.documentElement).getPropertyValue(v).trim();

    const draw = () => {
      const { serverNow, anchorWall } = clock.current;
      const virtualNow =
        serverNow > 0 ? serverNow + (performance.now() - anchorWall) / 1000 : 0;
      const windowStart = virtualNow - WINDOW_S;

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

        const buf = buffers.current[t.key];
        // Age out samples that scrolled past the left edge.
        while (buf.length && buf[0].t < windowStart) buf.shift();
        if (buf.length < 2 || virtualNow === 0) continue;

        let lo = Infinity;
        let hi = -Infinity;
        for (const s of buf) {
          if (s.v < lo) lo = s.v;
          if (s.v > hi) hi = s.v;
        }
        const pad = (hi - lo) * 0.15 || 0.5;
        lo -= pad;
        hi += pad;
        const span = hi - lo || 1;

        g.strokeStyle = `hsl(${css(t.cssVar)})`;
        g.lineWidth = 1.5;
        g.lineJoin = "round";
        g.beginPath();
        let pen = false;
        for (let i = 0; i < buf.length; i++) {
          const x = ((buf[i].t - windowStart) / WINDOW_S) * w;
          const y = h - ((buf[i].v - lo) / span) * h;
          // Lift the pen across gaps so an absence renders as a hole in the
          // trace, not a line glossing over it.
          if (i > 0 && buf[i].t - buf[i - 1].t > 0.5) pen = false;
          if (pen) g.lineTo(x, y);
          else g.moveTo(x, y);
          pen = true;
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
    <div className="relative space-y-4">
      {present === false && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded bg-background/70 backdrop-blur-[2px]">
          <div className="text-center">
            <p className="text-sm font-semibold text-warning">No one in range</p>
            <p className="mt-1 text-xs text-muted-foreground">
              The radar sees an empty room. Waveforms resume when someone is present.
            </p>
          </div>
        </div>
      )}
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
