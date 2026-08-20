const { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, Button, StepProgress, FeatureItem, SensorItem, TextField, Logo, Badge } = window.KnightWatcherDesignSystem_3ee9cb;

const STEPS = ["welcome", "name", "sensors", "notifications", "test", "complete"];

function SetupScreen({ onExit }) {
  const [step, setStep] = React.useState(0);
  const [name, setName] = React.useState("");
  const [channels, setChannels] = React.useState({ sound: true, push: false });
  const key = STEPS[step];
  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "40px 24px", display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "center" }}><Logo size={28} /></div>
      {key !== "complete" && <StepProgress current={step + 1} total={STEPS.length} />}

      {key === "welcome" && (
        <Card>
          <CardHeader style={{ textAlign: "center", alignItems: "center" }}>
            <CardTitle>Welcome to KnightWatcher</CardTitle>
            <CardDescription>Let&apos;s set up your monitoring system in just a few steps</CardDescription>
          </CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <FeatureItem icon={<Icon name="CircleCheck" size={20} />} title="Non-invasive monitoring" description="No wearables needed — monitors breathing and movement from a distance" />
            <FeatureItem icon={<Icon name="Bell" size={20} />} title="Instant alerts" description="Get notified immediately if something needs your attention" />
            <FeatureItem icon={<Icon name="Lock" size={20} />} title="Private & secure" description="All data stays on your device — no cloud required" />
          </CardContent>
          <CardFooter><Button size="lg" style={{ width: "100%" }} onClick={next}>Get Started</Button></CardFooter>
        </Card>
      )}

      {key === "name" && (
        <Card>
          <CardHeader><CardTitle>Who are we watching?</CardTitle><CardDescription>This name appears on alerts and in the dashboard</CardDescription></CardHeader>
          <CardContent><TextField value={name} onChange={setName} placeholder="Miles" leadingIcon={<Icon name="User" size={16} />} /></CardContent>
          <CardFooter style={{ gap: 8 }}>
            <Button variant="outline" style={{ flex: 1 }} onClick={back}>Back</Button>
            <Button style={{ flex: 1 }} onClick={next} disabled={!name.trim()}>Continue</Button>
          </CardFooter>
        </Card>
      )}

      {key === "sensors" && (
        <Card>
          <CardHeader><CardTitle>Position your sensors</CardTitle><CardDescription>Make sure the sensors can see the bed clearly</CardDescription></CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <SensorItem name="Radar Sensor" description="Detects breathing and movement" detected signal={85} required icon={<Icon name="Check" size={20} />} />
              <SensorItem name="Audio Sensor" description="Listens for breathing sounds" detected icon={<Icon name="Check" size={20} />} />
              <SensorItem name="BCG Sensor" description="Measures heart rate via mattress" optional icon={<Icon name="X" size={20} />} />
            </div>
            <div style={{ borderRadius: "var(--radius-lg)", padding: 16, background: "rgba(30,41,59,.5)", display: "flex", flexDirection: "column", gap: 8 }}>
              <h4 style={{ margin: 0, fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)" }}>Positioning tips:</h4>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: "var(--text-sm)", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: 4 }}>
                <li>Mount radar sensor on wall facing the bed</li>
                <li>Keep 1-2 meters from the bed for best results</li>
                <li>Avoid obstructions between sensor and bed</li>
              </ul>
            </div>
          </CardContent>
          <CardFooter style={{ gap: 8 }}>
            <Button variant="outline" style={{ flex: 1 }} onClick={back}>Back</Button>
            <Button style={{ flex: 1 }} onClick={next}>Looks Good</Button>
          </CardFooter>
        </Card>
      )}

      {key === "notifications" && (
        <Card>
          <CardHeader><CardTitle>How should we reach you?</CardTitle><CardDescription>Alerts fire the moment a reading leaves its safe range</CardDescription></CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[["sound", "Speaker alarm", "Sounds on the device by the bed"], ["push", "Push notification", "Sent to your phone over your local network"]].map(([k, t, d]) => (
              <button key={k} onClick={() => setChannels((c) => ({ ...c, [k]: !c[k] }))}
                style={{ display: "flex", alignItems: "center", gap: 12, padding: 16, textAlign: "left", cursor: "pointer", borderRadius: "var(--radius-lg)", background: channels[k] ? "var(--fill-accent)" : "var(--surface-card)", border: "1px solid " + (channels[k] ? "var(--accent-primary)" : "var(--border-default)"), color: "var(--text-primary)", fontFamily: "var(--font-body)" }}>
                <span style={{ width: 40, height: 40, borderRadius: "var(--radius-full)", display: "inline-flex", alignItems: "center", justifyContent: "center", background: channels[k] ? "rgba(124,58,237,.25)" : "var(--surface-muted)", color: channels[k] ? "var(--accent-primary)" : "var(--text-muted)" }}>
                  <Icon name={k === "sound" ? "Volume2" : "Smartphone"} size={20} />
                </span>
                <span style={{ flex: 1 }}>
                  <span style={{ display: "block", fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)" }}>{t}</span>
                  <span style={{ display: "block", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{d}</span>
                </span>
                {channels[k] && <Icon name="Check" size={18} style={{ color: "var(--accent-primary)" }} />}
              </button>
            ))}
          </CardContent>
          <CardFooter style={{ gap: 8 }}>
            <Button variant="outline" style={{ flex: 1 }} onClick={back}>Back</Button>
            <Button style={{ flex: 1 }} onClick={next}>Continue</Button>
          </CardFooter>
        </Card>
      )}

      {key === "test" && (
        <Card>
          <CardHeader><CardTitle>Test the alarm</CardTitle><CardDescription>Play a test alert so you know what to listen for</CardDescription></CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: 16, borderRadius: "var(--radius-lg)", border: "1px solid var(--border-default)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Icon name="Volume2" size={20} style={{ color: "var(--accent-primary)" }} />
                <span style={{ fontSize: "var(--text-sm)" }}>Speaker alarm</span>
              </div>
              <Button variant="outline" size="sm">Play test</Button>
            </div>
            <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
              KnightWatcher is not a medical device. It should supplement, not replace, proper medical supervision.
            </p>
          </CardContent>
          <CardFooter style={{ gap: 8 }}>
            <Button variant="outline" style={{ flex: 1 }} onClick={back}>Back</Button>
            <Button style={{ flex: 1 }} onClick={next}>Finish Setup</Button>
          </CardFooter>
        </Card>
      )}

      {key === "complete" && (
        <Card variant="success">
          <CardHeader style={{ textAlign: "center", alignItems: "center" }}>
            <span style={{ width: 56, height: 56, borderRadius: "var(--radius-full)", background: "rgba(22,163,74,.20)", color: "var(--status-normal)", display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 8 }}>
              <Icon name="Check" size={28} />
            </span>
            <CardTitle>You&apos;re all set</CardTitle>
            <CardDescription>KnightWatcher is now watching {name || "Miles"}. You can change any of this in Settings.</CardDescription>
          </CardHeader>
          <CardContent style={{ display: "flex", justifyContent: "center", gap: 8 }}>
            <Badge tone="normal">Radar online</Badge><Badge tone="normal">Audio online</Badge><Badge tone="neutral">BCG not connected</Badge>
          </CardContent>
          <CardFooter><Button size="lg" style={{ width: "100%" }} onClick={onExit}>Open Dashboard</Button></CardFooter>
        </Card>
      )}
    </div>
  );
}
Object.assign(window, { SetupScreen });
