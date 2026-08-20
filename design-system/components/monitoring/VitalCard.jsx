import React from "react";
import { Card, CardContent } from "../core/Card.jsx";

function statusOf(value, { normalRange, warningRange, criticalRange, status }) {
  if (typeof value !== "number") return status;
  if (criticalRange && (value < criticalRange.low || value > criticalRange.high)) return "critical";
  if (warningRange && (value < warningRange.low || value > warningRange.high)) return "warning";
  if (normalRange && value >= normalRange.min && value <= normalRange.max) return "normal";
  return status;
}

const CARD_VARIANT = { normal: "success", warning: "warning", alert: "critical", critical: "critical" };
const ICON_STYLE = {
  normal: { background: "rgba(22,163,74,.20)", color: "var(--status-normal)" },
  warning: { background: "rgba(250,204,21,.20)", color: "var(--status-warning)" },
  alert: { background: "rgba(239,68,68,.20)", color: "var(--status-critical)" },
  critical: { background: "rgba(239,68,68,.20)", color: "var(--status-critical)" },
  uncertain: { background: "var(--surface-muted)", color: "var(--text-muted)" },
};

export function VitalCard({ title, value, unit, icon, status = "uncertain", isLoading, normalRange, warningRange, criticalRange, showAsText, subtitle }) {
  const s = statusOf(value, { normalRange, warningRange, criticalRange, status });
  const valueColor = showAsText
    ? (s === "normal" ? "var(--status-normal)" : "var(--text-muted)")
    : s === "critical" ? "var(--status-critical)"
    : s === "warning" ? "var(--status-warning)"
    : (typeof value === "number" && normalRange && value >= normalRange.min && value <= normalRange.max) ? "var(--status-normal)"
    : "var(--text-primary)";
  const display = isLoading || value === null || value === undefined ? "—" : typeof value === "number" ? Math.round(value) : value;

  return (
    <Card variant={CARD_VARIANT[s] || "default"}>
      <CardContent style={{ padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{title}</span>
          <span style={{ display: "inline-flex", padding: 8, borderRadius: "var(--radius-full)", ...ICON_STYLE[s] || ICON_STYLE.uncertain }}>{icon}</span>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{ fontSize: "var(--text-4xl)", fontWeight: "var(--weight-bold)", fontVariantNumeric: "tabular-nums", letterSpacing: "var(--tracking-tight)", color: valueColor, opacity: isLoading ? 0.6 : 1 }}>{display}</span>
          {unit && !showAsText && <span style={{ fontSize: "var(--text-lg)", color: "var(--text-muted)" }}>{unit}</span>}
        </div>
        {subtitle
          ? <p style={{ margin: "4px 0 0", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{subtitle}</p>
          : normalRange && typeof value === "number"
            ? <p style={{ margin: "8px 0 0", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Normal: {normalRange.min}–{normalRange.max} {unit}</p>
            : null}
      </CardContent>
    </Card>
  );
}
