import type { NextConfig } from "next";

// Static export mode for WiFi setup pages (proctor, portal)
const isStaticExport = process.env.STATIC_EXPORT === "true";
// Portal build runs on Pi without basePath
const isPortalBuild = process.env.PORTAL_BUILD === "true";

const nextConfig: NextConfig = {
  // Switch between standalone (dashboard) and static export (wifi pages)
  output: isStaticExport ? "export" : "standalone",

  // Required for static export
  ...(isStaticExport && {
    // Only use basePath for GitHub Pages (proctor), not for Pi portal
    ...(isPortalBuild ? {} : { basePath: "/nightwatch/setup" }),
    images: { unoptimized: true },
    trailingSlash: true,
  }),

  // API proxy to Python backend during development (not used in static export)
  ...(!isStaticExport && {
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
  }),
};

export default nextConfig;
