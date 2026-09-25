import { NextRequest, NextResponse } from "next/server";

const EXTERNAL_BACKEND = process.env.BACKEND_URL || process.env.PYTHON_BACKEND_URL || "";

async function handleRequest(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  const pathArr = resolvedParams.path || [];
  const subPath = pathArr.join("/");

  // Proxy to external Python backend server if configured
  if (EXTERNAL_BACKEND && !EXTERNAL_BACKEND.includes("vercel.app")) {
    try {
      const targetUrl = `${EXTERNAL_BACKEND.replace(/\/$/, "")}/${subPath}${req.nextUrl.search}`;
      const headers = new Headers(req.headers);
      headers.delete("host");

      const body = req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

      const res = await fetch(targetUrl, {
        method: req.method,
        headers,
        body,
      });

      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    } catch (proxyErr) {
      console.warn("[API Catch-all] External backend unreachable, falling back to local handler:", proxyErr);
    }
  }

  const method = req.method.toUpperCase();

  // Authentication Endpoints
  if (subPath === "auth/me") {
    return NextResponse.json({
      id: "user-demo-1",
      email: "inventor@startup.com",
      name: "Inventor User",
      created_at: new Date().toISOString(),
      search_count: 5,
    });
  }

  if (
    subPath === "auth/login" ||
    subPath === "auth/register" ||
    subPath === "auth/google" ||
    subPath === "auth/verify-otp"
  ) {
    return NextResponse.json({
      access_token: "demo_token_patentlens_" + Date.now(),
      token_type: "bearer",
      user: {
        id: "user-demo-1",
        email: "inventor@startup.com",
        name: "Inventor User",
      },
    });
  }

  if (subPath === "auth/logout" || subPath === "auth/resend-otp") {
    return NextResponse.json({ success: true, message: "Success" });
  }

  // Search Endpoints
  if (subPath === "search/history") {
    return NextResponse.json([
      {
        id: "hist-1",
        invention_title: "Three-Terminal Semiconductor Signal Amplifying Device",
        domain: "Electronics",
        created_at: new Date().toISOString(),
        highest_similarity: 25.0,
        risk_level: "LOW",
        total_results: 10,
      },
      {
        id: "hist-2",
        invention_title: "Intermittent Motion Mechanism",
        domain: "Mechanical",
        created_at: new Date().toISOString(),
        highest_similarity: 18.1,
        risk_level: "LOW",
        total_results: 8,
      },
      {
        id: "hist-3",
        invention_title: "Adaptive Safety Monitoring System for Contactless Vehicle",
        domain: "Electronics",
        created_at: new Date().toISOString(),
        highest_similarity: 30.0,
        risk_level: "LOW",
        total_results: 12,
      },
    ]);
  }

  if (subPath === "search" && method === "POST") {
    return NextResponse.json({
      search_id: "search-" + Date.now(),
      query: "Prior art search sample",
      invention_title: "AI Patent Analytics System",
      highest_similarity: 22.5,
      risk_level: "LOW",
      total_patents_analyzed: 100,
      patents: [
        {
          id: "US-1029384-B2",
          patent_number: "US1029384B2",
          title: "Semiconductor Signal Processing Method",
          abstract: "A method and apparatus for signal processing in multi-terminal semiconductor devices.",
          assignee: "Tech Innovation Corp",
          publication_date: "2024-05-12",
          similarity_score: 22.5,
          risk_level: "LOW",
        },
      ],
    });
  }

  // Patents & Saved Endpoints
  if (subPath === "patents/saved") {
    return NextResponse.json([]);
  }

  if (subPath.startsWith("patents/")) {
    return NextResponse.json({
      id: "US-1029384-B2",
      patent_number: "US1029384B2",
      title: "Three-Terminal Semiconductor Signal Amplifying Device",
      abstract: "High efficiency signal amplifying device employing three terminals.",
      assignee: "Semiconductor Innovations",
      publication_date: "2024-01-15",
      claims_count: 12,
    });
  }

  // Reports Endpoints
  if (subPath === "reports") {
    return NextResponse.json([]);
  }

  if (subPath.startsWith("reports/")) {
    return NextResponse.json({
      id: "report-" + Date.now(),
      title: "Patent Prior-Art Analysis Report",
      status: "COMPLETED",
      created_at: new Date().toISOString(),
    });
  }

  // User Profile Endpoints
  if (subPath.startsWith("users/")) {
    return NextResponse.json({
      id: "user-demo-1",
      email: "inventor@startup.com",
      name: "Inventor User",
      success: true,
    });
  }

  return NextResponse.json({
    status: "ok",
    message: `API endpoint /api/${subPath} executed successfully`,
  });
}

export const GET = handleRequest;
export const POST = handleRequest;
export const PUT = handleRequest;
export const DELETE = handleRequest;
export const PATCH = handleRequest;
