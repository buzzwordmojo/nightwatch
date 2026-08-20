The loudest element in the product — one banner per unresolved alert, stacked above the vitals grid.

```jsx
<AlertBanner level="critical" message="No respiration detected" source="radar" time="2:14 AM"
  icon={<XCircle size={24} />} onAcknowledge={ack} onResolve={resolve} />
```

Acknowledging stops the pulse but keeps the banner; resolving removes it. Never show more than the real alerts — no placeholder banners.
