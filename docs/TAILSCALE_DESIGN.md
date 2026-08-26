# Remote access via Tailscale — plan

Status: **planned 2026-08-25, not installed.** Optional; monitoring must never
depend on it.

## What problem this actually solves

Not alerting. ntfy already reaches a phone from anywhere over public HTTPS, and
that must stay true — an alert path that requires the phone to be on a mesh VPN
is an alert path that fails when the VPN does. **Tailscale is for reaching the
device, not for alarms.**

What it fixes:

| Today | With the Pi on the tailnet |
|---|---|
| Dashboard only from the home WiFi | Dashboard from anywhere, phone or laptop |
| Support means "get on the right SSID first" | SSH from any machine on the tailnet |
| LAN address chased across DHCP leases | stable `nightwatch` MagicDNS name |
| No way to check the monitored person from away | remote view works |
| No path in if home routing breaks | independent path in |

## Existing tailnet

If you already run a tailnet with MagicDNS enabled, adding the monitor is
joining a mesh rather than standing one up. Phones need to be members too if
you want the dashboard remotely.

## Design rules

1. **Monitoring never depends on the tailnet.** Detection, alert evaluation and
   ntfy publishing all continue if `tailscaled` is dead. Nothing in the
   monitoring path may resolve a `100.x` address or a MagicDNS name.
2. **The dead man's switch stays off-tailnet.** It reports to API Gateway over
   the public internet. Routing the watchdog through the mesh would mean a
   tailnet failure silences the thing whose job is noticing silence.
3. **Least privilege via ACL tags.** Tag the Pi (e.g. `tag:nightwatch`) and
   allow only what is needed: dashboard 443 and SSH 22 from Bob's devices.
   The Pi should not be able to initiate connections *to* other tailnet nodes;
   it is the most physically exposed device on the network and sits in a
   child's bedroom.
4. **Do not use Tailscale SSH's `check` mode on the monitor.** Plain `ssh` and
   `scp` hang forever at the userauth banner waiting for a browser re-auth that
   never arrives in an automated context. Use
   `"action": "accept"` for `tag:nightwatch`, or leave Tailscale SSH off
   entirely and keep key-based OpenSSH.
5. **Resource cost is real but small** — `tailscaled` is ~30-50 MB RSS. The Pi
   has 7 GB free. Acceptable; worth re-checking after install.
6. **Update surface.** Tailscale is another package that wants updating. Pin
   it, and fold it into the OTA thinking rather than letting it auto-upgrade
   underneath a monitoring device.

## Install sketch

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=nightwatch --advertise-tags=tag:nightwatch --ssh=false
```

Then in the admin console: approve the node, confirm the tag, and add ACL
grants for 22/443 from your user. MagicDNS gives `nightwatch.<tailnet>.ts.net`.

Optionally `tailscale cert` for a real TLS certificate on that name, which
would retire the self-signed CA warning — but only after the CA question is
settled, since the current cert is what phones already trust.

## What it does NOT change

- **Alerts still require the ntfy app on the phones.** This plan does not move
  that forward by a single step.
- Local access keeps working exactly as now; the LAN path is unaffected.
- The 60 GHz sensing, the lock quality, the mounting — untouched.

## Open questions

- Put phones on the tailnet too? Needed for remote dashboard, but a phone
  that routes through a mesh has its own battery and connectivity trade-offs.
  Alerts must not care either way.
- Use `tailscale cert` and retire the self-signed CA, or keep the CA so the
  LAN path and the remote path present the same certificate?
- Should the OTA pull-check run over the tailnet or the public internet? Public
  is more robust for the same reason the watchdog is.
