import React from "react";

export function FeatureItem({ icon, title, description }) {
  return (
    <div style={{ display: "flex", gap: 12 }}>
      <span style={{ flexShrink: 0, width: 40, height: 40, borderRadius: "var(--radius-full)", background: "var(--fill-accent)", color: "var(--accent-primary)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{icon}</span>
      <div>
        <h3 style={{ margin: 0, fontSize: "var(--text-base)", fontWeight: "var(--weight-medium)" }}>{title}</h3>
        <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{description}</p>
      </div>
    </div>
  );
}
