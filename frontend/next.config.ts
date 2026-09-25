import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const rawUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "").trim();

    // Do NOT rewrite if empty, pointing to self, or pointing to vercel.app without dedicated backend domain
    if (!rawUrl || rawUrl.includes("vercel.app") || rawUrl === "/api" || rawUrl === "api") {
      return [];
    }

    let targetUrl = rawUrl;
    if (!targetUrl.startsWith("http://") && !targetUrl.startsWith("https://")) {
      targetUrl = `https://${targetUrl}`;
    }
    targetUrl = targetUrl.endsWith("/api") ? targetUrl : `${targetUrl.replace(/\/$/, "")}/api`;

    return [
      {
        source: "/api/:path*",
        destination: `${targetUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
