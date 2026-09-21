import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "https://automated-patent-prior-art-search-vb4c-l24fdcigj.vercel.app/api";
    const targetUrl = backendUrl.endsWith("/api") ? backendUrl : `${backendUrl.replace(/\/$/, "")}/api`;
    return [
      {
        source: "/api/:path*",
        destination: `${targetUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
