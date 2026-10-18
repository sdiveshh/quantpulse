export const dynamic = "force-dynamic";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

async function forward(request, context) {
  const { path } = await context.params;
  const segments = path || [];
  if (segments.some((s) => s === "" || s === "." || s === "..")) {
    return Response.json({ detail: "Bad path" }, { status: 400 });
  }
  const safe = segments.map(encodeURIComponent).join("/");
  const url = `${BACKEND}/api/${safe}${new URL(request.url).search}`;

  const headers = { "Content-Type": "application/json" };
  if (process.env.API_KEY) headers["X-API-Key"] = process.env.API_KEY;

  const init = { method: request.method, headers, cache: "no-store" };
  if (request.method === "POST") init.body = await request.text();

  try {
    const upstream = await fetch(url, init);
    const out = {
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    };
    const retry = upstream.headers.get("retry-after");
    if (retry) out["Retry-After"] = retry;
    return new Response(upstream.body, { status: upstream.status, headers: out });
  } catch {
    return Response.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}

export const GET = forward;
export const POST = forward;