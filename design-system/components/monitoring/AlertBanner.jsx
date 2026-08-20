import React from "react";
import { Button } from "../core/Button.jsx";

export function AlertBanner({ level = "warning", message, source, time, acknowledged, icon, onAcknowledge, onResolve }) {
  const critical = level === "critical";
  const color = critical ? "var(--status-critical)" : "var(--status-warning)";
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16,
      padding: 16, borderRadius: "var(--radius-lg)",
      border: "1px solid " + (critical ? "var(--border-critical)" : "var(--border-warning)"),
      background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)",
      animation: acknowledged ? "none" : "kw-pulse-slow 1s var(--ease-standard) infinite",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ color, display: "inline-flex" }}>{icon}</span>
        <div>
          <p style={{ margin: 0, fontWeight: "var(--weight-medium)", color }}>{message}</p>
          <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
            {source}{time ? " • " + time : ""}{acknowledged ? " • Acknowledged" : ""}
          </p>
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
        {!acknowledged && <Button variant="outline" size="sm" onClick={onAcknowledge}>Acknowledge</Button>}
        <Button variant={critical ? "danger" : "warning"} size="sm" onClick={onResolve}>Resolve</Button>
      </div>
    </div>
  );
}
