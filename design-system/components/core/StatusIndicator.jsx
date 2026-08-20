import React from "react";

const COLORS = {
  online: "var(--status-normal)", normal: "var(--status-normal)",
  warning: "var(--status-warning)", degraded: "var(--status-warning)", stale: "var(--status-warning)",
  error: "var(--status-critical)", alert: "var(--status-critical)", critical: "var(--status-critical)", offline: "var(--status-critical)",
};
const SIZES = { sm: 8, md: 12, lg: 16 };

export function StatusIndicator({ status = "offline", label, size = "md" }) {
  const live = status === "normal" || status === "online";
  const d = SIZES[size] || SIZES.md;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{
        width: d, height: d, borderRadius: "var(--radius-full)", flexShrink: 0,
        background: COLORS[status] || "var(--status-offline)",
        animation: live ? "kw-pulse-ring var(--dur-pulse-slow) var(--ease-standard) infinite" : status === "stale" ? "kw-pulse-slow 2s var(--ease-standard) infinite" : "none",
      }} />
      {label && (
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", textTransform: "capitalize" }}>{label}: {status}</span>
      )}
    </div>
  );
}
