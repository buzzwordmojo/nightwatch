import React from "react";
import { Button } from "../core/Button.jsx";

const OPTIONS = [
  { minutes: 5, label: "Pause for 5 minutes" },
  { minutes: 15, label: "Pause for 15 minutes" },
  { minutes: 30, label: "Pause for 30 minutes" },
  { minutes: 60, label: "Pause for 1 hour" },
];

export function PauseButton({ isPaused, remainingMinutes, onPause, onResume, pauseIcon, playIcon }) {
  const [open, setOpen] = React.useState(false);
  if (isPaused) {
    return <Button variant="warning" size="sm" onClick={onResume}>{playIcon}Resume ({remainingMinutes}m)</Button>;
  }
  return (
    <div style={{ position: "relative" }}>
      <Button variant="outline" size="sm" onClick={() => setOpen(!open)}>{pauseIcon}Pause</Button>
      {open && (
        <div style={{ position: "absolute", right: 0, top: "calc(100% + 4px)", zIndex: 20, minWidth: 190, padding: 4, borderRadius: "var(--radius-md)", border: "1px solid var(--border-default)", background: "var(--surface-card)", boxShadow: "var(--shadow-lg)" }}>
          {OPTIONS.map((o) => (
            <button key={o.minutes} onClick={() => { setOpen(false); onPause && onPause(o.minutes); }}
              style={{ display: "block", width: "100%", textAlign: "left", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "none", background: "transparent", color: "var(--text-primary)", fontFamily: "var(--font-body)", fontSize: "var(--text-sm)", cursor: "pointer" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-muted)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>{o.label}</button>
          ))}
        </div>
      )}
    </div>
  );
}
