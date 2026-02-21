"use client";

import { ConvexProvider as BaseConvexProvider, ConvexReactClient } from "convex/react";
import { ReactNode, useMemo } from "react";

// Only create client if URL is configured (not during static export)
const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL;

export function ConvexProvider({ children }: { children: ReactNode }) {
  const client = useMemo(() => {
    if (!convexUrl) return null;
    return new ConvexReactClient(convexUrl);
  }, []);

  // During static export or when Convex is not configured, render children directly
  if (!client) {
    return <>{children}</>;
  }

  return <BaseConvexProvider client={client}>{children}</BaseConvexProvider>;
}
