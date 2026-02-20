import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: "standalone",

  // API proxy to Python backend during development
  async rewrites() {
    return [
      {
        source: "/api/nightwatch/:path*",
        destination: "http://localhost:9531/api/:path*",
      },
      {
        source: "/api/setup/:path*",
        destination: "http://localhost:9531/api/setup/:path*",
      },
      {
        source: "/ws",
        destination: "http://localhost:9531/ws",
      },
    ];
  },
};

export default nextConfig;
