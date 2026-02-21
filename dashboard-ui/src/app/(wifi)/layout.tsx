import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nightwatch Setup",
  description: "Set up your Nightwatch device",
};

export default function WifiLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <div className="container max-w-md mx-auto px-4 py-8">
        {/* Logo Header */}
        <header className="text-center mb-8">
          <h1 className="text-2xl font-bold text-primary">Nightwatch</h1>
          <p className="text-muted-foreground text-sm">Setup Wizard</p>
        </header>
        {children}
      </div>
    </div>
  );
}
