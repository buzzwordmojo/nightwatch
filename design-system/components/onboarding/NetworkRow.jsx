import React from "react";

export function NetworkRow({ ssid, signal = 0, secured, selected, onSelect, icon, lockIcon }) {
  const label = signal >= 70 ? "Strong" : signal >= 40 ? "Good" : "Weak";
  return (
    <button onClick={onSelect} style={{
      width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: 16, borderRadius: "var(--radius-lg)", cursor: "pointer",
      background: selected ? "var(--fill-accent)" : "var(--surface-card)",
      border: "1px solid " + (selected ? "var(--accent-primary)" : "var(--border-default)"),
      boxShadow: selected ? "0 0 0 2px rgba(124,58,237,.25)" : "none",
      color: "var(--text-primary)", fontFamily: "var(--font-body)",
      transition: "all var(--dur-base) var(--ease-standard)",
    }}>
      <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ display: "inline-flex", color: signal >= 70 ? "var(--status-normal)" : signal >= 40 ? "var(--status-warning)" : "var(--text-muted)" }}>{icon}</span>
        <span style={{ textAlign: "left" }}>
          <span style={{ display: "block", fontWeight: "var(--weight-medium)" }}>{ssid}</span>
          <span style={{ display: "block", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{label} signal</span>
        </span>
      </span>
      <span style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)", fontSize: "var(--text-sm)" }}>
        {secured && lockIcon}
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{signal}%</span>
      </span>
    </button>
  );
}
