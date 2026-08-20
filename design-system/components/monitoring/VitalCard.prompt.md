One card per vital — heart rate, respiration, breathing, bed status. Four across on desktop, one per row on mobile.

```jsx
<VitalCard title="Respiration" value={16} unit="BPM" icon={<Wind size={20} />}
  status="normal" normalRange={{min:10,max:25}} warningRange={{low:6,high:30}} criticalRange={{low:4,high:35}} />
<VitalCard title="Bed Status" value="Occupied" icon={<Moon size={20} />} status="normal" showAsText />
```

Value is 36px bold tabular; the card border and fill inherit the derived status, so a warning card pulses without any extra markup.
