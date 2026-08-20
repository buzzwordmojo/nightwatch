import React from "react";

export function StepProgress({ current = 1, total = 6 }) {
  const pct = Math.min(100, Math.max(0, (current / total) * 100));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ height: 8, borderRadius: "var(--radius-full)", background: "var(--surface-muted)", overflow: "hidden" }}>
        <div style={{ height: "100%", width: pct + "%", background: "var(--accent-primary)", borderRadius: "var(--radius-full)", transition: "width var(--dur-slow) var(--ease-standard)" }} />
      </div>
      <p style={{ margin: 0, textAlign: "center", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Step {current} of {total}</p>
    </div>
  );
}
