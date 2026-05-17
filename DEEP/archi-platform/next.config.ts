import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  bundlePagesRouterDependencies: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  allowedDevOrigins: ["192.168.11.100"],
  experimental: {
    turbo: {
      rules: {},
    },
  },
};

export default nextConfig;
