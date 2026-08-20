import React from "react";

export function Progress({ value = 0, tone = "accent", height = 8, style }) {
  const pct = Math.min(100, Math.max(0, value));
  const fill = { accent: "var(--accent-primary)", normal: "var(--status-normal)", warning: "var(--status-warning)", critical: "var(--status-critical)" }[tone] || "var(--accent-primary)";
  return (
    <div style={{ position: "relative", height, width: "100%", overflow: "hidden", borderRadius: "var(--radius-full)", background: "var(--surface-muted)", ...style }}>
      <div style={{ height: "100%", width: pct + "%", background: fill, borderRadius: "var(--radius-full)", transition: "width var(--dur-base) var(--ease-standard)" }} />
    </div>
  );
}
