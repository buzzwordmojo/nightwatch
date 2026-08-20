Every panel in KnightWatcher is a Card — 8px radius, 1px border, near-black fill; the status variants are reserved for surfaces that report a live sensor state.

```jsx
<Card variant="success">
  <CardHeader><CardTitle>Respiration</CardTitle><CardDescription>Radar · 92% confidence</CardDescription></CardHeader>
  <CardContent>…</CardContent>
</Card>
```

Variants: default, success (green tint), warning (amber tint, slow pulse), critical (red tint, fast pulse + shadow). Sub-parts: CardHeader, CardTitle, CardDescription, CardContent, CardFooter — all 24px padding.
