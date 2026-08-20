const { Card, CardHeader, CardTitle, CardContent, CardFooter, Button, NetworkRow, TextField, Logo, StatusIndicator } = window.KnightWatcherDesignSystem_3ee9cb;

const NETWORKS = [
  { ssid: "Home-5G", signal: 82, secured: true },
  { ssid: "Home-2.4G", signal: 64, secured: true },
  { ssid: "Nest-Guest", signal: 41, secured: true },
  { ssid: "xfinitywifi", signal: 22, secured: false },
];

function PortalScreen() {
  const [step, setStep] = React.useState("connect-hotspot");
  const [ssid, setSsid] = React.useState(null);
  const [password, setPassword] = React.useState("");
  const [show, setShow] = React.useState(false);

  return (
    <div style={{ maxWidth: 440, margin: "0 auto", padding: "32px 20px", display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", justifyContent: "center" }}><Logo size={26} /></div>

      {step === "connect-hotspot" && (
        <Card>
          <CardHeader style={{ paddingBottom: 16 }}>
            <CardTitle style={{ fontSize: "var(--text-lg)", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 32, height: 32, borderRadius: "var(--radius-full)", background: "var(--fill-accent)", color: "var(--accent-primary)", fontSize: "var(--text-sm)", fontWeight: "var(--weight-bold)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>1</span>
              Connect to KnightWatcher
            </CardTitle>
          </CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div style={{ background: "rgba(30,41,59,.5)", borderRadius: "var(--radius-lg)", padding: 16, textAlign: "center" }}>
              <p style={{ margin: "0 0 4px", fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "var(--tracking-wider)" }}>WiFi Network Name</p>
              <p style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "var(--text-xl)", fontWeight: "var(--weight-bold)", color: "var(--accent-primary)" }}>knightwatcher-a4f1</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[["Settings", "Open your phone's Settings app"], ["Wifi", "Go to WiFi settings"], ["Smartphone", "Select knightwatcher-a4f1 and connect"]].map(([ic, t]) => (
                <div key={ic} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                  <span style={{ flexShrink: 0, width: 24, height: 24, borderRadius: "var(--radius-full)", background: "var(--surface-muted)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name={ic} size={12} /></span>
                  <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>{t}</p>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter><Button style={{ width: "100%" }} onClick={() => setStep("select-network")}>I&apos;m connected</Button></CardFooter>
        </Card>
      )}

      {step === "select-network" && (
        <Card>
          <CardHeader><CardTitle style={{ fontSize: "var(--text-lg)" }}>Choose your home network</CardTitle></CardHeader>
          <CardContent style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {NETWORKS.map((n) => (
              <NetworkRow key={n.ssid} {...n} selected={ssid === n.ssid} onSelect={() => setSsid(n.ssid)}
                icon={<Icon name={n.signal >= 40 ? "Wifi" : "WifiOff"} size={16} />} lockIcon={<Icon name="Lock" size={12} />} />
            ))}
            <button onClick={() => {}} style={{ alignSelf: "center", marginTop: 4, border: "none", background: "transparent", color: "var(--accent-primary)", fontSize: "var(--text-sm)", fontFamily: "var(--font-body)", cursor: "pointer" }}>Scan again</button>
          </CardContent>
          <CardFooter><Button style={{ width: "100%" }} disabled={!ssid} onClick={() => setStep("password")}>Continue</Button></CardFooter>
        </Card>
      )}

      {step === "password" && (
        <Card>
          <CardHeader><CardTitle style={{ fontSize: "var(--text-lg)" }}>Password for {ssid}</CardTitle></CardHeader>
          <CardContent>
            <TextField type={show ? "text" : "password"} value={password} onChange={setPassword} placeholder="Enter password"
              leadingIcon={<Icon name="Lock" size={16} />} trailingIcon={<Icon name={show ? "EyeOff" : "Eye"} size={16} />} onTrailingClick={() => setShow(!show)}
              error={password.length > 0 && password.length < 8 ? "Password must be at least 8 characters" : null} />
          </CardContent>
          <CardFooter style={{ gap: 8 }}>
            <Button variant="outline" style={{ flex: 1 }} onClick={() => setStep("select-network")}>Back</Button>
            <Button style={{ flex: 1 }} disabled={password.length < 8} onClick={() => setStep("connecting")}>Connect</Button>
          </CardFooter>
        </Card>
      )}

      {step === "connecting" && (
        <Card>
          <CardContent style={{ padding: 40, textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
            <span style={{ color: "var(--accent-primary)", animation: "kw-pulse-slow 2s var(--ease-standard) infinite" }}><Icon name="Wifi" size={32} /></span>
            <div>
              <p style={{ margin: 0, fontWeight: "var(--weight-medium)" }}>Joining {ssid}…</p>
              <p style={{ margin: "4px 0 0", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>The hotspot will shut down in 30 seconds</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => setStep("complete")}>Skip ahead</Button>
          </CardContent>
        </Card>
      )}

      {step === "complete" && (
        <Card variant="success">
          <CardContent style={{ padding: 32, textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <span style={{ width: 48, height: 48, borderRadius: "var(--radius-full)", background: "rgba(22,163,74,.20)", color: "var(--status-normal)", display: "inline-flex", alignItems: "center", justifyContent: "center" }}><Icon name="Check" size={24} /></span>
            <p style={{ margin: 0, fontWeight: "var(--weight-medium)" }}>Connected to {ssid}</p>
            <p style={{ margin: 0, fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>https://knightwatcher.local</p>
            <StatusIndicator status="online" label="Device" />
            <Button style={{ width: "100%", marginTop: 8 }} onClick={() => setStep("connect-hotspot")}>Open Dashboard</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
Object.assign(window, { PortalScreen });
