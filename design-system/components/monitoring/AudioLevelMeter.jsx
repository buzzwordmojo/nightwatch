import React from "react";

export function AudioLevelMeter({ level = 0, peak }) {
  const pct = Math.min(100, Math.max(0, level * 100));
  const peakPct = peak != null ? Math.min(100, Math.max(0, peak * 100)) : 0;
  const color = pct > 70 ? "var(--status-critical)" : pct > 40 ? "var(--status-warning)" : "var(--status-normal)";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
        <span>Audio Level</span>
        <span style={{ fontFamily: "var(--font-mono)" }}>{pct.toFixed(0)}%</span>
      </div>
      <div style={{ position: "relative", height: 12, borderRadius: "var(--radius-full)", overflow: "hidden", background: "var(--surface-muted)" }}>
        <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: pct + "%", background: color, borderRadius: "var(--radius-full)", transition: "width 75ms linear" }} />
        {peakPct > pct + 2 && <div style={{ position: "absolute", top: 0, bottom: 0, width: 2, left: peakPct + "%", background: "rgba(255,255,255,.7)" }} />}
        <div style={{ position: "absolute", inset: 0, display: "flex" }}>
          {[0, 1, 2].map((i) => <div key={i} style={{ flex: 1, borderRight: "1px solid rgba(2,8,23,.2)" }} />)}
          <div style={{ flex: 1 }} />
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--text-2xs)", color: "rgba(148,163,184,.6)", padding: "0 2px" }}>
        {["0", "25", "50", "75", "100"].map((t) => <span key={t}>{t}</span>)}
      </div>
    </div>
  );
}
