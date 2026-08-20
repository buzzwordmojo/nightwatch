import React from "react";

const TONES = {
  neutral: { background: "var(--surface-muted)", color: "var(--text-muted)" },
  accent: { background: "var(--fill-accent)", color: "var(--accent-primary)" },
  normal: { background: "rgba(22,163,74,.20)", color: "var(--status-normal)" },
  warning: { background: "rgba(250,204,21,.20)", color: "var(--status-warning)" },
  critical: { background: "rgba(239,68,68,.20)", color: "var(--status-critical)" },
  simulated: { background: "var(--status-simulated)", color: "var(--text-inverse)" },
};

export function Badge({ tone = "neutral", uppercase = false, style, children, ...rest }) {
  return (
    <span {...rest} style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: uppercase ? "2px 6px" : "4px 8px",
      borderRadius: "var(--radius-sm)",
      fontFamily: "var(--font-body)",
      fontSize: uppercase ? "var(--text-2xs)" : "var(--text-xs)",
      fontWeight: uppercase ? "var(--weight-bold)" : "var(--weight-medium)",
      textTransform: uppercase ? "uppercase" : "none",
      letterSpacing: uppercase ? "var(--tracking-wide)" : "var(--tracking-normal)",
      lineHeight: 1.4,
      ...TONES[tone] || TONES.neutral, ...style,
    }}>{children}</span>
  );
}
