// KnightWatcher brand lockup, ported from design-system/components/brand/Logo.jsx.
// Inline SVG on purpose: it must render with no network and no asset pipeline.

interface LogoProps {
  size?: number;
  variant?: "lockup" | "mark" | "wordmark";
  className?: string;
}

export function Logo({ size = 32, variant = "lockup", className }: LogoProps) {
  const mark = (
    <svg
      viewBox="0 0 48 56"
      width={size * 0.857}
      height={size}
      fill="none"
      className="shrink-0"
      aria-hidden="true"
    >
      <path
        d="M24 2.6 44.4 11.2v18.4c0 13.1-9 21.7-20.4 25.4C12.6 51.3 3.6 42.7 3.6 29.6V11.2z"
        stroke="var(--brand-purple)"
        strokeWidth="3.4"
        strokeLinejoin="round"
      />
      <path
        d="M27.6 17.6a10 10 0 1 0 0 20 12.6 12.6 0 0 1 0-20z"
        fill="var(--brand-yellow)"
      />
    </svg>
  );
  const word = (
    <span
      className="whitespace-nowrap font-display font-bold tracking-tight"
      style={{ fontSize: size * 0.72, lineHeight: 1 }}
    >
      Knight<span style={{ color: "var(--brand-purple)" }}>Watcher</span>
    </span>
  );
  return (
    <span className={`inline-flex items-center text-foreground ${className ?? ""}`} style={{ gap: size * 0.35 }}>
      {variant !== "wordmark" && mark}
      {variant !== "mark" && word}
    </span>
  );
}
