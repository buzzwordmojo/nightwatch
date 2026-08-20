const { Logo, Button, Card, CardContent, Badge, FeatureItem, VitalCard, StatusIndicator } = window.KnightWatcherDesignSystem_3ee9cb;

function Nav() {
  return (
    <header style={{ position: "sticky", top: 0, zIndex: 10, borderBottom: "1px solid var(--border-default)", background: "rgba(2,8,23,.8)", backdropFilter: "blur(8px)" }}>
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Logo size={26} />
        <nav style={{ display: "flex", alignItems: "center", gap: 24, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
          <a href="#how">How it works</a><a href="#sensors">Sensors</a><a href="#build">Build one</a>
          <Button variant="outline" size="sm"><Icon name="Github" size={14} />GitHub</Button>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section style={{ maxWidth: 1120, margin: "0 auto", padding: "80px 24px 64px", display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 56, alignItems: "center" }}>
      <div>
        <Badge tone="accent">Open source · MIT</Badge>
        <h1 style={{ margin: "16px 0 0", fontSize: 56, lineHeight: 1.05, letterSpacing: "var(--tracking-tight)", fontWeight: "var(--weight-bold)" }}>
          Non-contact seizure monitoring for the room you can&apos;t sit in all night
        </h1>
        <p style={{ margin: "20px 0 0", fontSize: "var(--text-lg)", lineHeight: "var(--leading-relaxed)", color: "var(--text-muted)", maxWidth: 520, textWrap: "pretty" }}>
          KnightWatcher watches a sleeping child for signs of seizure activity using radar, audio, and bed vibration. Nothing is attached to them, and nothing leaves the house.
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 32 }}>
          <Button size="lg">Build your own</Button>
          <Button variant="outline" size="lg"><Icon name="BookOpen" size={16} />Read the docs</Button>
        </div>
        <p style={{ margin: "20px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Runs on a Raspberry Pi 5. About $123 in parts.</p>
      </div>
      <Card><CardContent style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Tonight · 2:16 AM</span>
          <StatusIndicator status="online" label="System" />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <VitalCard title="Heart Rate" value={72} unit="BPM" icon={<Icon name="Heart" size={20} />} status="normal" normalRange={{ min: 50, max: 100 }} />
          <VitalCard title="Respiration" value={16} unit="BPM" icon={<Icon name="Wind" size={20} />} status="normal" normalRange={{ min: 10, max: 25 }} />
        </div>
        <div style={{ padding: 14, borderRadius: "var(--radius-lg)", border: "1px solid var(--border-normal)", background: "var(--fill-normal)", textAlign: "center", animation: "kw-breathing-glow 4s var(--ease-standard) infinite" }}>
          <span style={{ color: "var(--status-normal)", fontWeight: "var(--weight-medium)" }}>All clear — breathing steady</span>
        </div>
      </CardContent></Card>
    </section>
  );
}

function HowItWorks() {
  return (
    <section id="how" style={{ borderTop: "1px solid var(--border-default)", borderBottom: "1px solid var(--border-default)", background: "var(--surface-card)" }}>
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "64px 24px", display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 32 }}>
        <FeatureItem icon={<Icon name="Radio" size={20} />} title="Non-contact monitoring" description="Nothing is attached to the child. Sensors sit on the wall and the nightstand." />
        <FeatureItem icon={<Icon name="Bell" size={20} />} title="Real-time alerts" description="A speaker alarm by the bed, plus push notifications while you're out." />
        <FeatureItem icon={<Icon name="Lock" size={20} />} title="Stays in your house" description="All processing happens on the Pi. Remote access runs over Tailscale — no cloud service." />
      </div>
    </section>
  );
}

const SENSORS = [
  { icon: "Radio", name: "Radar", detects: "Respiration rate, movement, presence", hw: "HLK-LD2450 (24GHz mmWave)", status: "Testing soon" },
  { icon: "Mic", name: "Audio", detects: "Breathing sounds, seizure sounds, silence", hw: "Lavalier / USB microphone", status: "Testing soon" },
  { icon: "Activity", name: "Capacitive", detects: "Heart rate, respiration, bed occupancy", hw: "FDC1004 + electrode", status: "Planned" },
];

function Sensors() {
  return (
    <section id="sensors" style={{ maxWidth: 1120, margin: "0 auto", padding: "72px 24px" }}>
      <h2 style={{ margin: 0, fontSize: 36, letterSpacing: "var(--tracking-tight)", fontWeight: "var(--weight-bold)" }}>Three sensors, one picture</h2>
      <p style={{ margin: "12px 0 32px", color: "var(--text-muted)", maxWidth: 620, textWrap: "pretty" }}>
        Each detector publishes to an event bus; a fusion engine combines them, so one noisy signal doesn&apos;t raise a false alarm on its own.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {SENSORS.map((s) => (
          <Card key={s.name}><CardContent style={{ padding: 24, display: "flex", flexDirection: "column", gap: 12 }}>
            <span style={{ width: 40, height: 40, borderRadius: "var(--radius-full)", background: "var(--fill-accent)", color: "var(--accent-primary)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name={s.icon} size={20} /></span>
            <div>
              <h3 style={{ margin: 0, fontSize: "var(--text-xl)", fontWeight: "var(--weight-semibold)" }}>{s.name}</h3>
              <p style={{ margin: "6px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{s.detects}</p>
            </div>
            <p style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{s.hw}</p>
            <Badge tone="neutral">{s.status}</Badge>
          </CardContent></Card>
        ))}
      </div>
    </section>
  );
}

function Build() {
  return (
    <section id="build" style={{ borderTop: "1px solid var(--border-default)", background: "var(--surface-card)" }}>
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "64px 24px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 36, letterSpacing: "var(--tracking-tight)", fontWeight: "var(--weight-bold)" }}>Build one this weekend</h2>
          <p style={{ margin: "12px 0 24px", color: "var(--text-muted)", textWrap: "pretty" }}>
            Clone the repo, install the Python package, and run it with mock sensors before any hardware arrives. Enclosure STLs and a full shopping list are in the repo.
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <Button><Icon name="Github" size={16} />Clone the repo</Button>
            <Button variant="outline">Shopping list</Button>
          </div>
        </div>
        <div style={{ padding: 20, borderRadius: "var(--radius-lg)", border: "1px solid var(--border-default)", background: "var(--surface-app)", fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", lineHeight: 1.8 }}>
          <div style={{ color: "var(--text-muted)" }}># install</div>
          <div>pip install -e .</div>
          <div style={{ color: "var(--text-muted)", marginTop: 8 }}># run with mock sensors</div>
          <div>./bin/mock</div>
          <div style={{ color: "var(--text-muted)", marginTop: 8 }}># dashboard</div>
          <div>http://localhost:3000</div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer style={{ borderTop: "1px solid var(--border-default)" }}>
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "40px 24px", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 32 }}>
        <div>
          <Logo size={22} />
          <p style={{ margin: "12px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)", maxWidth: 460 }}>
            KnightWatcher is not a medical device. It should supplement, not replace, proper medical supervision.
          </p>
        </div>
        <div style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)", textAlign: "right", lineHeight: 1.9 }}>
          <div><a href="#how">Docs</a></div><div><a href="#sensors">Sensors</a></div><div><a href="#build">GitHub</a></div>
          <div style={{ marginTop: 12 }}>MIT License</div>
        </div>
      </div>
    </footer>
  );
}

function LandingPage() {
  return <div><Nav /><Hero /><HowItWorks /><Sensors /><Build /><Footer /></div>;
}
Object.assign(window, { LandingPage });
