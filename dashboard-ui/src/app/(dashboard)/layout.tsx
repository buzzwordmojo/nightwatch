"use client";

import { ConvexProvider } from "@/components/providers/ConvexProvider";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ConvexProvider>{children}</ConvexProvider>;
}
