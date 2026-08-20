import React from "react";

export function TextField({ value, onChange, placeholder, type = "text", leadingIcon, trailingIcon, onTrailingClick, error, disabled }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ position: "relative" }}>
        {leadingIcon && <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", display: "inline-flex" }}>{leadingIcon}</span>}
        <input type={type} value={value} placeholder={placeholder} disabled={disabled}
          onChange={(e) => onChange && onChange(e.target.value)}
          style={{
            width: "100%", boxSizing: "border-box",
            padding: `12px ${trailingIcon ? 48 : 12}px 12px ${leadingIcon ? 40 : 12}px`,
            borderRadius: "var(--radius-lg)", background: "var(--surface-card)",
            border: "1px solid " + (error ? "var(--red-600)" : "var(--border-default)"),
            color: "var(--text-primary)", fontFamily: "var(--font-body)", fontSize: "var(--text-base)",
            outline: "none", opacity: disabled ? 0.5 : 1,
          }}
          onFocus={(e) => { e.target.style.borderColor = error ? "var(--red-600)" : "var(--accent-primary)"; e.target.style.boxShadow = `0 0 0 2px ${error ? "rgba(209,43,43,.5)" : "rgba(124,58,237,.5)"}`; }}
          onBlur={(e) => { e.target.style.borderColor = error ? "var(--red-600)" : "var(--border-default)"; e.target.style.boxShadow = "none"; }} />
        {trailingIcon && (
          <button type="button" onClick={onTrailingClick} disabled={disabled}
            style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", border: "none", background: "transparent", color: "var(--text-muted)", cursor: "pointer", display: "inline-flex", padding: 0 }}>{trailingIcon}</button>
        )}
      </div>
      {error && <p style={{ margin: 0, fontSize: "var(--text-xs)", color: "var(--red-600)" }}>{error}</p>}
    </div>
  );
}
