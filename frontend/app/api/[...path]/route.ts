import { NextRequest, NextResponse } from "next/server";

// Environment variable for Python backend server URL
// Priority: BACKEND_URL -> PYTHON_BACKEND_URL -> http://127.0.0.1:8000
const EXTERNAL_BACKEND = process.env.BACKEND_URL || process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000";

async function handleRequest(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  const pathArr = resolvedParams.path || [];
  const subPath = pathArr.join("/");

  try {
    let baseUrl = EXTERNAL_BACKEND.replace(/\/$/, "");
    let cleanSubPath = subPath.startsWith("/") ? subPath.slice(1) : subPath;

    // Ensure /api prefix is present when forwarding to backend
    if (!baseUrl.endsWith("/api") && !cleanSubPath.startsWith("api/")) {
      cleanSubPath = `api/${cleanSubPath}`;
    }

    const targetUrl = `${baseUrl}/${cleanSubPath}${req.nextUrl.search}`;
    const headers = new Headers(req.headers);
    headers.delete("host");

    const body = req.method !== "GET" && req.method !== "HEAD" ? await req.text() : undefined;

    const res = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
    });

    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    } else {
      const text = await res.text();
      return new NextResponse(text, {
        status: res.status,
        headers: {
          "content-type": contentType || "text/plain",
        },
      });
    }
  } catch (proxyErr: any) {
    console.error(`[API Proxy Error] Failed to connect to backend target (${EXTERNAL_BACKEND}):`, proxyErr);
    return NextResponse.json(
      {
        detail: "Backend service unavailable. Failed to reach Python backend server.",
        backend_url: EXTERNAL_BACKEND,
        error: String(proxyErr),
      },
      { status: 502 }
    );
  }
}

export const GET = handleRequest;
export const POST = handleRequest;
export const PUT = handleRequest;
export const DELETE = handleRequest;
export const PATCH = handleRequest;
