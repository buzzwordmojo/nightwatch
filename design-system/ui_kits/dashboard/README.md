# Dashboard UI kit

Recreation of the KnightWatcher device dashboard — the Next.js app at `nightwatch/dashboard-ui`, rebranded.

| File | Source it recreates |
| --- | --- |
| `DashboardScreen.jsx` | `src/components/dashboard/DashboardView.tsx` + `VitalsChart`, `EventsList` |
| `SetupScreen.jsx` | `src/app/(dashboard)/setup/page.tsx` + `src/components/setup/*` |
| `SettingsScreen.jsx` | `src/app/(dashboard)/settings/layout.tsx` + `settings/page.tsx` |
| `PortalScreen.jsx` | `src/app/(wifi)/portal` + `src/components/wifi/*` |
| `icon.jsx` | lucide-react → lucide UMD wrapper |

`index.html` is the click-through: switch screens with the pill bar, trigger a critical alert, pause monitoring, step through the six-step wizard, and complete the Wi-Fi portal flow.

Not recreated: the radar aiming view, the certificate install/trust cards, and the notifications/sharing/updates settings panels (the Settings screen shows an explicit placeholder for those).
