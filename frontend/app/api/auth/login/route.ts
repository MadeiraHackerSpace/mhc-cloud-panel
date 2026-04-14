import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = (await req.json()) as { email: string; password: string };
  const secure = process.env.COOKIE_SECURE === "true";
  const base =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";

  let res: Response;
  try {
    res = await fetch(`${base}/api/v1/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body)
    });
  } catch {
    const demoUsers = new Set([
      "superadmin@mhc.local",
      "operador@mhc.local",
      "cliente@mhc.local"
    ]);
    if (demoUsers.has(body.email) && body.password === "admin12345") {
      const jar = cookies();
      jar.set("mhc_demo", "1", {
        httpOnly: true,
        sameSite: "lax",
        secure,
        path: "/"
      });
      jar.set("mhc_access_token", "demo", {
        httpOnly: true,
        sameSite: "lax",
        secure,
        path: "/"
      });
      jar.set("mhc_refresh_token", "demo", {
        httpOnly: true,
        sameSite: "lax",
        secure,
        path: "/"
      });
      return NextResponse.json({ ok: true, demo: true });
    }

    return NextResponse.json(
      {
        error: {
          message:
            "Backend indisponível. Inicie o backend (ex.: docker compose up) e tente novamente."
        }
      },
      { status: 503 }
    );
  }

  const data = await res.json().catch(() => null);
  if (!res.ok || !data?.access_token || !data?.refresh_token) {
    return NextResponse.json(
      { error: data?.error || { message: "Falha ao autenticar" } },
      { status: res.status || 401 }
    );
  }

  const jar = cookies();
  jar.set("mhc_access_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/"
  });
  jar.set("mhc_refresh_token", data.refresh_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/"
  });

  return NextResponse.json({ ok: true });
}
