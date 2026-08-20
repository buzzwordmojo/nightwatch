import React from "react";

const SIZES = {
  default: { height: 40, padding: "0 16px" },
  sm: { height: 36, padding: "0 12px" },
  lg: { height: 44, padding: "0 32px" },
  icon: { height: 40, width: 40, padding: 0 },
};

const VARIANTS = {
  default: { background: "var(--accent-primary)", color: "var(--text-on-accent)", border: "1px solid transparent" },
  destructive: { background: "var(--red-600)", color: "#fff", border: "1px solid transparent" },
  outline: { background: "transparent", color: "var(--text-primary)", border: "1px solid var(--border-default)" },
  secondary: { background: "var(--surface-muted)", color: "var(--text-primary)", border: "1px solid transparent" },
  ghost: { background: "transparent", color: "var(--text-primary)", border: "1px solid transparent" },
  link: { background: "transparent", color: "var(--accent-primary)", border: "1px solid transparent", textDecoration: "underline", textUnderlineOffset: 4 },
  success: { background: "var(--status-normal)", color: "#fff", border: "1px solid transparent" },
  warning: { background: "var(--status-warning)", color: "#000", border: "1px solid transparent" },
  danger: { background: "var(--status-critical)", color: "#fff", border: "1px solid transparent" },
};

export function Button({ variant = "default", size = "default", disabled, style, children, ...rest }) {
  const [hover, setHover] = React.useState(false);
  const v = VARIANTS[variant] || VARIANTS.default;
  return (
    <button
      {...rest}
      disabled={disabled}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8,
        whiteSpace: "nowrap", borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-body)", fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)",
        transition: "background var(--dur-fast) var(--ease-standard), color var(--dur-fast) var(--ease-standard), border-color var(--dur-fast) var(--ease-standard)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        filter: hover && !disabled && variant !== "outline" && variant !== "ghost" && variant !== "link" ? "brightness(0.9)" : "none",
        ...(hover && !disabled && (variant === "outline" || variant === "ghost") ? { background: "var(--surface-muted)" } : null),
        ...SIZES[size], ...v, ...style,
      }}
    >
      {children}
    </button>
  );
}
