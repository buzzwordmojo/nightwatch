"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ConvexProvider } from "@/components/providers/ConvexProvider";

function SetupGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const setupComplete = localStorage.getItem("nightwatch_setup_complete");
    if (!setupComplete) {
      router.replace("/proctor");
    } else {
      setIsReady(true);
    }
  }, [router]);

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ConvexProvider>
      <SetupGuard>{children}</SetupGuard>
    </ConvexProvider>
  );
}
