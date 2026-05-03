import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST() {
  const jar = cookies();
  const secure = process.env.COOKIE_SECURE !== "false";
  if (jar.get("mhc_demo")?.value === "1") {
    return NextResponse.json({ ok: true });
  }
  const refresh = jar.get("mhc_refresh_token")?.value;
  if (!refresh) return NextResponse.json({ ok: false }, { status: 401 });

  const base =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";
  let res: Response;
  try {
    res = await fetch(`${base}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh })
    });
  } catch {
    jar.delete("mhc_access_token");
    jar.delete("mhc_refresh_token");
    return NextResponse.json({ ok: false }, { status: 503 });
  }

  const data = await res.json().catch(() => null);
  if (!res.ok || !data?.access_token || !data?.refresh_token) {
    jar.delete("mhc_access_token");
    jar.delete("mhc_refresh_token");
    return NextResponse.json({ ok: false }, { status: 401 });
  }

  jar.set("mhc_access_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: 60 * 15 // 15 minutes, aligned with JWT_ACCESS_TOKEN_EXPIRES_MINUTES
  });
  jar.set("mhc_refresh_token", data.refresh_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: 60 * 60 * 24 * 30 // 30 days, aligned with JWT_REFRESH_TOKEN_EXPIRES_DAYS
  });

  return NextResponse.json({ ok: true });
}
