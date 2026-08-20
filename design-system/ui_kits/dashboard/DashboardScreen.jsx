const { VitalCard, AlertBanner, SensorStatusBar, AudioLevelMeter, EventRow, PauseButton, StatusIndicator, Card, CardContent, Logo, Button } = window.KnightWatcherDesignSystem_3ee9cb;

function VitalsChart({ points }) {
  const w = 1000, h = 180;
  const line = (vals, color, min, max, band) => {
    const [lo, hi] = band;
    const d = vals.map((v, i) => `${i === 0 ? "M" : "L"}${(i / (vals.length - 1)) * w},${h - (lo + ((v - min) / (max - min)) * (hi - lo)) * h}`).join(" ");
    return <path d={d} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />;
  };
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: "var(--text-lg)", fontWeight: "var(--weight-medium)" }}>Last 30 minutes</h2>
        <div style={{ display: "flex", gap: 16, fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 2, background: "var(--accent-primary)" }} />Respiration</span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 2, background: "var(--status-normal)" }} />Heart rate</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: 180, display: "block" }}>
        {[0.25, 0.5, 0.75].map((g) => <line key={g} x1="0" x2={w} y1={h * g} y2={h * g} stroke="var(--border-default)" strokeWidth="1" />)}
        {line(points.resp, "var(--accent-primary)", 8, 26, [0.06, 0.42])}
        {line(points.hr, "var(--status-normal)", 60, 84, [0.58, 0.94])}
      </svg>
    </div>
  );
}

function DashboardScreen({ state, onNavigate }) {
  const { vitals, alerts, paused, remaining, sensors, audioLevel } = state;
  return (
    <main style={{ minHeight: "100%", padding: 32 }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32, gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Logo size={30} />
          <div style={{ borderLeft: "1px solid var(--border-default)", paddingLeft: 16 }}>
            <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Last update: 2:16:04 AM</p>
          </div>
          <div style={{ borderLeft: "1px solid var(--border-default)", paddingLeft: 16 }}>
            <SensorStatusBar sensors={sensors} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <StatusIndicator status="online" label="System" />
          <PauseButton isPaused={paused} remainingMinutes={remaining} onPause={state.pause} onResume={state.resume}
            pauseIcon={<Icon name="Pause" size={16} />} playIcon={<Icon name="Play" size={16} />} />
          <button onClick={() => onNavigate("settings")} title="Settings"
            style={{ display: "inline-flex", padding: 8, borderRadius: "var(--radius-md)", border: "none", background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>
            <Icon name="Settings" size={20} />
          </button>
        </div>
      </header>

      {alerts.map((a) => (
        <div key={a.id} style={{ marginBottom: 12 }}>
          <AlertBanner {...a} icon={<Icon name={a.level === "critical" ? "XCircle" : "AlertTriangle"} size={24} />}
            onAcknowledge={() => state.acknowledge(a.id)} onResolve={() => state.resolve(a.id)} />
        </div>
      ))}

      {paused && (
        <div style={{ marginBottom: 24, padding: 16, borderRadius: "var(--radius-lg)", textAlign: "center", background: "rgba(250,204,21,.20)", border: "1px solid var(--border-warning)" }}>
          <p style={{ margin: 0, color: "var(--status-warning)", fontWeight: "var(--weight-medium)" }}>Monitoring paused for {remaining} more minutes</p>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32, marginTop: alerts.length ? 24 : 0 }}>
        <VitalCard title="Heart Rate" value={vitals.hr} unit="BPM" icon={<Icon name="Heart" size={20} />} status="normal" normalRange={{ min: 50, max: 100 }} warningRange={{ low: 40, high: 120 }} criticalRange={{ low: 35, high: 150 }} />
        <VitalCard title="Respiration" value={vitals.resp} unit="BPM" icon={<Icon name="Wind" size={20} />} status="normal" normalRange={{ min: 10, max: 25 }} warningRange={{ low: 6, high: 30 }} criticalRange={{ low: 4, high: 35 }} subtitle="2 sensors · 94% agree" />
        <VitalCard title="Breathing" value={vitals.breathing ? "Detected" : "—"} icon={<Icon name="Activity" size={20} />} status={vitals.breathing ? "normal" : "uncertain"} showAsText />
        <VitalCard title="Bed Status" value="Occupied" icon={<Icon name="Moon" size={20} />} status="normal" showAsText />
      </div>

      <Card><CardContent style={{ padding: 24 }}><VitalsChart points={state.series} /></CardContent></Card>

      <div style={{ marginTop: 16 }}>
        <Card><CardContent style={{ padding: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ flex: 1 }}><AudioLevelMeter level={audioLevel} peak={audioLevel + 0.12} /></div>
            <Button variant={state.listening ? "default" : "secondary"} size="sm" onClick={state.toggleListen}>
              <Icon name={state.listening ? "Volume2" : "VolumeX"} size={14} />{state.listening ? "Live" : "Listen"}
            </Button>
          </div>
        </CardContent></Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 32 }}>
        {[{ k: "radar", c: 0.94 }, { k: "audio", c: 0.81 }, { k: "bcg", c: null }].map(({ k, c }) => (
          <Card key={k}><CardContent style={{ padding: 16, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <p style={{ margin: 0, fontWeight: "var(--weight-medium)", textTransform: "capitalize" }}>{k} Detector</p>
              <p style={{ margin: "2px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Confidence: {c ? Math.round(c * 100) + "%" : "—"}</p>
            </div>
            <StatusIndicator status={c ? "normal" : "offline"} />
          </CardContent></Card>
        ))}
      </div>

      <div style={{ marginTop: 32 }}>
        <h2 style={{ margin: "0 0 12px", fontSize: "var(--text-lg)", fontWeight: "var(--weight-medium)" }}>Last 24 hours</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {state.events.length === 0 ? (
            <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-muted)" }}>
              <Icon name="Activity" size={32} style={{ opacity: 0.5, justifyContent: "center" }} />
              <p style={{ margin: "8px 0 0" }}>No alerts in the last 24 hours</p>
            </div>
          ) : state.events.map((e) => (
            <EventRow key={e.id} {...e} icon={<Icon name={e.level === "critical" ? "XCircle" : "AlertTriangle"} size={16} />} />
          ))}
        </div>
      </div>
    </main>
  );
}
Object.assign(window, { DashboardScreen });
