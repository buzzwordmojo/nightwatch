import React from "react";

function dotColor(sensor, mock) {
  if (mock) return "var(--status-simulated)";
  if (!sensor || !sensor.connected) return "rgba(148,163,184,.5)";
  if (["running", "online", "normal"].includes(sensor.status)) return "var(--status-normal)";
  if (["warning", "degraded", "uncertain"].includes(sensor.status)) return "var(--status-warning)";
  if (["error", "critical", "alert"].includes(sensor.status)) return "var(--status-critical)";
  return "rgba(148,163,184,.5)";
}

export function SensorStatusBar({ sensors = [] }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      {sensors.map((s) => {
        const connected = s.connected ?? false;
        return (
          <span key={s.key} title={s.label} style={{
            display: "inline-flex", alignItems: "center", gap: 4, padding: "2px 6px",
            borderRadius: "var(--radius-sm)", fontSize: "var(--text-xs)",
            color: connected ? "var(--text-primary)" : "var(--text-muted)",
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: "var(--radius-full)", flexShrink: 0, background: dotColor(s, s.mock),
              animation: connected && !s.mock && (s.status === "running" || s.status === "normal") ? "kw-pulse-slow 2s var(--ease-standard) infinite" : "none",
            }} />
            {s.icon}
            <span>{s.label}</span>
            {s.mock && (
              <span style={{ padding: "1px 4px", fontSize: 9, fontWeight: "var(--weight-bold)", lineHeight: 1.2, borderRadius: "var(--radius-sm)", background: "var(--status-simulated)", color: "var(--text-inverse)" }}>SIM</span>
            )}
          </span>
        );
      })}
    </div>
  );
}
