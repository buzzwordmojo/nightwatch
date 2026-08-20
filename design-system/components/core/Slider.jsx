import React from "react";

export function Slider({ value = 50, min = 0, max = 100, step = 1, onChange, label, valueLabel, disabled }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ width: "100%", opacity: disabled ? 0.5 : 1 }}>
      {(label || valueLabel) && (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: "var(--text-sm)" }}>
          <span style={{ color: "var(--text-muted)" }}>{label}</span>
          <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{valueLabel ?? value}</span>
        </div>
      )}
      <div style={{ position: "relative", height: 20, display: "flex", alignItems: "center" }}>
        <div style={{ position: "absolute", inset: "auto 0", height: 6, borderRadius: "var(--radius-full)", background: "var(--surface-muted)" }} />
        <div style={{ position: "absolute", left: 0, width: pct + "%", height: 6, borderRadius: "var(--radius-full)", background: "var(--accent-primary)" }} />
        <div style={{ position: "absolute", left: `calc(${pct}% - 8px)`, width: 16, height: 16, borderRadius: "var(--radius-full)", background: "var(--text-primary)", border: "2px solid var(--accent-primary)", boxShadow: "var(--shadow-sm)" }} />
        <input type="range" value={value} min={min} max={max} step={step} disabled={disabled}
          onChange={(e) => onChange && onChange(Number(e.target.value))}
          style={{ position: "absolute", inset: 0, width: "100%", opacity: 0, cursor: disabled ? "not-allowed" : "pointer", margin: 0 }} />
      </div>
    </div>
  );
}
