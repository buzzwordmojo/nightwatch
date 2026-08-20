Header-level sensor roll-call: one dot + label per detector, violet SIM chip when the data is simulated.

```jsx
<SensorStatusBar sensors={[
  {key:"radar", label:"Radar", icon:<Radio size={12}/>, connected:true, status:"running"},
  {key:"audio", label:"Audio", icon:<Mic size={12}/>, connected:true, status:"running", mock:true},
  {key:"bcg", label:"BCG", icon:<Activity size={12}/>, connected:false},
]} />
```
