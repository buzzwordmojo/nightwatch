import React from "react";
import { Badge } from "../core/Badge.jsx";

export function SensorItem({ name, description, detected, signal, required, optional, icon }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12, padding: 12, borderRadius: "var(--radius-lg)",
      border: "1px solid " + (detected ? "rgba(22,163,74,.30)" : "var(--border-default)"),
      background: detected ? "rgba(22,163,74,.05)" : "transparent",
    }}>
      <span style={{
        flexShrink: 0, width: 40, height: 40, borderRadius: "var(--radius-full)", display: "inline-flex", alignItems: "center", justifyContent: "center",
        background: detected ? "rgba(22,163,74,.20)" : "var(--surface-muted)",
        color: detected ? "var(--status-normal)" : "var(--text-muted)",
      }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)" }}>{name}</span>
          {required && <Badge tone="accent">Required</Badge>}
          {optional && <Badge tone="neutral">Optional</Badge>}
        </div>
        <p style={{ margin: "2px 0 0", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{description}</p>
      </div>
      {detected && signal !== undefined && (
        <div style={{ flexShrink: 0, textAlign: "right" }}>
          <div style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", fontVariantNumeric: "tabular-nums" }}>{signal}%</div>
          <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Signal</div>
        </div>
      )}
    </div>
  );
}
