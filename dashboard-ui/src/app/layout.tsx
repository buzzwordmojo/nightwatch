import type { Metadata } from "next";
import { ConvexProvider } from "@/components/providers/ConvexProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nightwatch",
  description: "Sleep monitoring dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ConvexProvider>{children}</ConvexProvider>
      </body>
    </html>
  );
}
