import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const jar = cookies();
  if (jar.get("mhc_demo")?.value === "1") {
    const payload = await req.json().catch(() => ({}));
    return NextResponse.json({ ok: true, ticket: { id: "ticket-demo", ...payload } });
  }

  const access = jar.get("mhc_access_token")?.value;
  if (!access) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  const body = await req.json();
  const base =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";
  const res = await fetch(`${base}/api/v1/tickets`, {
    method: "POST",
    headers: { authorization: `Bearer ${access}`, "content-type": "application/json" },
    body: JSON.stringify(body)
  });
  const text = await res.text();
  return new NextResponse(text, { status: res.status, headers: { "content-type": "application/json" } });
}
