Wi-Fi picker row used by the captive portal the device serves from its own hotspot.

```jsx
<NetworkRow ssid="Home-5G" signal={82} secured selected onSelect={pick}
  icon={<Wifi size={16}/>} lockIcon={<Lock size={12}/>} />
```

Stack rows with 8px gaps. Scanning, error, and empty states are plain centred icon + caption blocks — don't fake network rows.
