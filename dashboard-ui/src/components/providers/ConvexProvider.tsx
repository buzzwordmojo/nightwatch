"use client";

import { ConvexProvider as BaseConvexProvider, ConvexReactClient } from "convex/react";
import { ReactNode, useMemo, useState, useEffect } from "react";

// Placeholder URL for SSR/build time - Convex client requires a valid URL format
const PLACEHOLDER_URL = "https://placeholder.convex.cloud";

export function ConvexProvider({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const client = useMemo(() => {
    // During SSR/build, use placeholder URL (won't actually connect)
    if (typeof window === "undefined") {
      return new ConvexReactClient(PLACEHOLDER_URL);
    }
    // In browser, use proxy through the Python server
    const protocol = window.location.protocol;
    const host = window.location.host;
    return new ConvexReactClient(`${protocol}//${host}/convex`);
  }, []);

  // Show loading state until mounted in browser
  if (!mounted) {
    return (
      <BaseConvexProvider client={client}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </div>
      </BaseConvexProvider>
    );
  }

  return <BaseConvexProvider client={client}>{children}</BaseConvexProvider>;
}
