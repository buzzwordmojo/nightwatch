import React from "react";

const SOURCE_LABELS = { radar: "Breathing", audio: "Audio", bcg: "Heart Rate", movement: "Movement" };

export function EventRow({ source, level = "warning", message, startTime, endTime, duration, ongoing, count = 1, icon }) {
  const critical = level === "critical" || level === "alert";
  const color = critical ? "var(--status-critical)" : "var(--status-warning)";
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: 12, padding: 12,
      borderRadius: "var(--radius-lg)",
      border: "1px solid " + (critical ? "rgba(239,68,68,.30)" : "rgba(250,204,21,.30)"),
      background: critical ? "var(--fill-critical)" : "var(--fill-warning)",
      animation: ongoing ? "kw-pulse-slow var(--dur-pulse-slow) var(--ease-standard) infinite" : "none",
    }}>
      <span style={{ display: "inline-flex", padding: 8, borderRadius: "var(--radius-full)", flexShrink: 0, background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)", color }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{ fontWeight: "var(--weight-medium)", color }}>{SOURCE_LABELS[source] || source}</span>
          <span style={{ fontSize: "var(--text-xs)", textTransform: "uppercase", padding: "2px 8px", borderRadius: "var(--radius-full)", background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)", color }}>{level}</span>
        </div>
        <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{message}</p>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4, fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
          <span>{startTime}</span>
          {ongoing
            ? <span style={{ fontWeight: "var(--weight-medium)", color }}>ongoing</span>
            : <><span>-</span><span>{endTime}</span>{duration && <span style={{ color: "rgba(248,250,252,.6)" }}>({duration})</span>}</>}
          {count > 1 && <span style={{ color: "rgba(248,250,252,.4)" }}>• {count} events</span>}
        </div>
      </div>
    </div>
  );
}
