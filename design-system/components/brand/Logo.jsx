import React from "react";

export function Logo({ size = 32, variant = "lockup", accent = "var(--brand-purple)", moon = "var(--brand-yellow)", style }) {
  const mark = (
    <svg viewBox="0 0 48 56" width={size * 0.857} height={size} fill="none" style={{ flexShrink: 0 }} aria-hidden="true">
      <path d="M24 2.6 44.4 11.2v18.4c0 13.1-9 21.7-20.4 25.4C12.6 51.3 3.6 42.7 3.6 29.6V11.2z" stroke={accent} strokeWidth="3.4" strokeLinejoin="round" />
      <path d="M27.6 17.6a10 10 0 1 0 0 20 12.6 12.6 0 0 1 0-20z" fill={moon} />
    </svg>
  );
  const word = (
    <span style={{ fontFamily: "var(--font-display)", fontWeight: "var(--weight-bold)", fontSize: size * 0.72, letterSpacing: "var(--tracking-tight)", lineHeight: 1, whiteSpace: "nowrap" }}>
      Knight<span style={{ color: accent }}>Watcher</span>
    </span>
  );
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: size * 0.35, color: "var(--text-primary)", ...style }}>
      {variant !== "wordmark" && mark}
      {variant !== "mark" && word}
    </span>
  );
}
