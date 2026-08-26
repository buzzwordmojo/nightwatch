# Getting alerts on your phone (Android)

The monitor publishes alerts to our own private server at
`https://ntfy.<your-domain>` (your own server). Nothing here needs an account with any
company — the server is ours. Each phone needs about three minutes:

1. Install **ntfy** from the Play Store (by Philipp Heckel, free).
2. Open it → ⚙ Settings → **Default server** → `https://ntfy.<your-domain>` (your own server).
3. Still in Settings → **Manage users** → add user:
   - Username: `family`
   - Password: *(from your own credentials file, e.g.
     `~/.config/knightwatcher/ntfy.env`, line `NTFY_FAMILY_PASSWORD=`)*
4. Back on the main screen → **+ Subscribe to topic** → topic name: `alerts`
   → make sure it uses the knightwatcher server, not ntfy.sh.
5. **The two settings that make it work at 3am** (both required):
   - Settings → **Instant delivery** → ON. This keeps a connection open
     instead of relying on Google's push, which Android may delay for hours
     on a dozing phone.
   - Android Settings → Apps → ntfy → Notifications → the topic channel →
     **Override Do Not Disturb** → ON. Repeat on both phones.
6. Test: from the dev machine,
   `curl -u "pi:$NTFY_PI_PASSWORD" -H "Priority: 5" -d "test" https://ntfy.<your-domain>/alerts`
   — the phone should sound even in DND.

Battery optimisation may need to be disabled for ntfy
(Settings → Apps → ntfy → Battery → Unrestricted) or Android will
eventually kill the instant-delivery connection.
