const { Card, CardContent, Button, Slider, StatusIndicator, Badge, Logo } = window.KnightWatcherDesignSystem_3ee9cb;

const NAV = [
  { key: "general", label: "General", icon: "Settings" },
  { key: "radar", label: "Radar", icon: "Radio" },
  { key: "audio", label: "Audio", icon: "Mic" },
  { key: "notifications", label: "Notifications", icon: "Bell" },
  { key: "sharing", label: "Sharing", icon: "Users" },
  { key: "alerts", label: "Alert Rules", icon: "TriangleAlert" },
  { key: "updates", label: "Updates", icon: "Download" },
];

function Row({ icon, title, description, right }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ padding: 8, borderRadius: "var(--radius-full)", background: "var(--surface-muted)", color: "var(--text-muted)", display: "inline-flex" }}><Icon name={icon} size={16} /></span>
        <div>
          <p style={{ margin: 0, fontWeight: "var(--weight-medium)" }}>{title}</p>
          <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{description}</p>
        </div>
      </div>
      {right}
    </div>
  );
}

function SettingsScreen({ onBack }) {
  const [tab, setTab] = React.useState("general");
  const [gain, setGain] = React.useState(64);
  const [sensitivity, setSensitivity] = React.useState(70);

  return (
    <div style={{ minHeight: "100%" }}>
      <header style={{ borderBottom: "1px solid var(--border-default)", background: "var(--surface-card)" }}>
        <div style={{ maxWidth: 1024, margin: "0 auto", padding: "16px 16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <button onClick={onBack} style={{ display: "inline-flex", alignItems: "center", gap: 8, border: "none", background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>
              <Icon name="ArrowLeft" size={16} /><Logo variant="mark" size={22} />
            </button>
            <h1 style={{ margin: 0, fontSize: "var(--text-xl)", fontWeight: "var(--weight-semibold)" }}>Settings</h1>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: 1024, margin: "0 auto", padding: "24px 16px", display: "flex", gap: 24 }}>
        <nav style={{ width: 192, flexShrink: 0 }}>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 4 }}>
            {NAV.map((n) => (
              <li key={n.key}>
                <button onClick={() => setTab(n.key)} style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderRadius: "var(--radius-md)",
                  fontSize: "var(--text-sm)", fontFamily: "var(--font-body)", cursor: "pointer", border: "none", textAlign: "left",
                  background: tab === n.key ? "var(--surface-muted)" : "transparent",
                  color: tab === n.key ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: tab === n.key ? "var(--weight-medium)" : "var(--weight-regular)",
                }}><Icon name={n.icon} size={16} />{n.label}</button>
              </li>
            ))}
          </ul>
        </nav>

        <main style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 24 }}>
          {tab === "general" && (<>
            <div>
              <h2 style={{ margin: "0 0 4px", fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)" }}>General Settings</h2>
              <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>System status and device information</p>
            </div>
            <Card><CardContent style={{ padding: 24 }}>
              <h3 style={{ margin: "0 0 16px", fontWeight: "var(--weight-medium)" }}>System Status</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <Row icon="Wifi" title="Connection" description="Backend status" right={<Badge tone="normal">online</Badge>} />
                <Row icon="Clock" title="Last Update" description="Most recent data received" right={<span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Just now</span>} />
                <Row icon="HardDrive" title="Detectors" description="Active sensor count" right={<span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>3 active</span>} />
              </div>
            </CardContent></Card>
            <Card><CardContent style={{ padding: 24 }}>
              <h3 style={{ margin: "0 0 16px", fontWeight: "var(--weight-medium)" }}>Detector Status</h3>
              <div style={{ display: "flex", flexDirection: "column" }}>
                {[["radar", "online", "LD2450 on /dev/ttyUSB0"], ["audio", "online", "USB lavalier"], ["bcg", "offline", "No electrode detected"]].map(([n, s, m], i, arr) => (
                  <div key={n} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: i < arr.length - 1 ? "1px solid var(--border-default)" : "none" }}>
                    <div>
                      <p style={{ margin: 0, fontWeight: "var(--weight-medium)", textTransform: "capitalize" }}>{n}</p>
                      <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{m}</p>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <button title={`Restart ${n} detector`} style={{ padding: 6, borderRadius: "var(--radius-md)", border: "none", background: "transparent", color: "var(--text-muted)", cursor: "pointer", display: "inline-flex" }}><Icon name="RotateCw" size={16} /></button>
                      <Badge tone={s === "online" ? "normal" : "critical"}>{s}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent></Card>
            <p style={{ margin: 0, textAlign: "center", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>KnightWatcher v0.1.0</p>
          </>)}

          {tab === "audio" && (<>
            <div>
              <h2 style={{ margin: "0 0 4px", fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)" }}>Audio</h2>
              <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Microphone gain and breathing-sound thresholds</p>
            </div>
            <Card><CardContent style={{ padding: 24, display: "flex", flexDirection: "column", gap: 24 }}>
              <Slider label="Microphone gain" value={gain} onChange={setGain} valueLabel={gain + "%"} />
              <Slider label="Silence alert threshold" value={sensitivity} onChange={setSensitivity} valueLabel={sensitivity + "%"} />
              <Row icon="Mic" title="Live listen" description="Stream device audio to this browser" right={<Button variant="outline" size="sm">Listen</Button>} />
            </CardContent></Card>
          </>)}

          {tab === "alerts" && (<>
            <div>
              <h2 style={{ margin: "0 0 4px", fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)" }}>Alert Rules</h2>
              <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Conditions that raise a warning or critical alert</p>
            </div>
            <Card><CardContent style={{ padding: 0 }}>
              {[["respiration_low", "radar", "respiration_rate < 8", "15s", "warning"], ["respiration_absent", "radar", "respiration_rate < 4", "10s", "critical"], ["silence", "audio", "no breathing sound", "20s", "critical"]].map(([n, d, c, dur, lvl], i, arr) => (
                <div key={n} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 16, borderBottom: i < arr.length - 1 ? "1px solid var(--border-default)" : "none" }}>
                  <div>
                    <p style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)" }}>{n}</p>
                    <p style={{ margin: "4px 0 0", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{d} · {c} · for {dur}</p>
                  </div>
                  <Badge tone={lvl === "critical" ? "critical" : "warning"}>{lvl}</Badge>
                </div>
              ))}
            </CardContent></Card>
          </>)}

          {!["general", "audio", "alerts"].includes(tab) && (
            <Card><CardContent style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              <StatusIndicator status="offline" size="sm" />
              <p style={{ margin: "12px 0 0", fontSize: "var(--text-sm)" }}>The {NAV.find((n) => n.key === tab).label} panel is not recreated in this kit.</p>
            </CardContent></Card>
          )}
        </main>
      </div>
    </div>
  );
}
Object.assign(window, { SettingsScreen });
