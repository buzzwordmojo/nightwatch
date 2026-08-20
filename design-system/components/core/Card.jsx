import React from "react";

const VARIANTS = {
  default: { borderColor: "var(--border-default)", background: "var(--surface-card)" },
  success: { borderColor: "var(--border-normal)", background: "var(--fill-normal)" },
  warning: { borderColor: "var(--border-warning)", background: "var(--fill-warning)", animation: "kw-pulse-slow var(--dur-pulse-slow) var(--ease-standard) infinite" },
  critical: { borderColor: "var(--border-critical)", background: "var(--fill-critical)", animation: "kw-pulse-fast var(--dur-pulse-fast) var(--ease-standard) infinite", boxShadow: "var(--shadow-critical)" },
};

export function Card({ variant = "default", style, children, ...rest }) {
  return (
    <div {...rest} style={{
      borderRadius: "var(--radius-lg)", border: "1px solid", color: "var(--text-primary)",
      boxShadow: "var(--shadow-sm)", transition: "all var(--dur-slow) var(--ease-standard)",
      ...VARIANTS[variant] || VARIANTS.default, ...style,
    }}>{children}</div>
  );
}

export function CardHeader({ style, children, ...rest }) {
  return <div {...rest} style={{ display: "flex", flexDirection: "column", gap: 6, padding: 24, ...style }}>{children}</div>;
}

export function CardTitle({ style, children, ...rest }) {
  return <h3 {...rest} style={{ margin: 0, fontFamily: "var(--font-display)", fontSize: "var(--text-2xl)", fontWeight: "var(--weight-semibold)", lineHeight: "var(--leading-none)", letterSpacing: "var(--tracking-tight)", ...style }}>{children}</h3>;
}

export function CardDescription({ style, children, ...rest }) {
  return <p {...rest} style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)", ...style }}>{children}</p>;
}

export function CardContent({ style, children, ...rest }) {
  return <div {...rest} style={{ padding: "0 24px 24px", ...style }}>{children}</div>;
}

export function CardFooter({ style, children, ...rest }) {
  return <div {...rest} style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 24px 24px", ...style }}>{children}</div>;
}
