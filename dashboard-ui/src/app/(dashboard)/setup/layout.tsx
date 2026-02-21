import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Setup - Nightwatch",
  description: "Set up your Nightwatch monitoring system",
};

export default function SetupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <div className="container mx-auto px-4 py-8 max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
            <svg
              className="w-8 h-8 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold">Nightwatch</h1>
          <p className="text-muted-foreground text-sm">
            Sleep monitoring for peace of mind
          </p>
        </div>

        {/* Content */}
        {children}
      </div>
    </div>
  );
}
