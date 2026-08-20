Row in the events history list. Stack rows with 8px gaps; show the empty state ("No alerts in the last 24 hours") rather than filler rows.

```jsx
<EventRow source="radar" level="warning" message="Respiration below 8 BPM"
  startTime="2:14 AM" endTime="2:15 AM" duration="1m 20s" count={3} icon={<AlertTriangle size={16}/>} />
```
