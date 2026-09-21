import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    let rawUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "").trim();
    if (!rawUrl) {
      rawUrl = "https://automated-patent-prior-art-search-vb4c-l24fdcigj.vercel.app/api";
    } else if (!rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
      rawUrl = `https://${rawUrl}`;
    }

    const targetUrl = rawUrl.endsWith("/api") ? rawUrl : `${rawUrl.replace(/\/$/, "")}/api`;

    return [
      {
        source: "/api/:path*",
        destination: `${targetUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
