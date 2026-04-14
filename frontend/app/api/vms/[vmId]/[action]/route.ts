import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(
  _req: Request,
  { params }: { params: { vmId: string; action: string } }
) {
  const action = params.action;
  if (!["start", "stop", "reboot"].includes(action)) {
    return NextResponse.json({ error: "invalid_action" }, { status: 400 });
  }

  const jar = cookies();
  if (jar.get("mhc_demo")?.value === "1") {
    return NextResponse.json({ ok: true });
  }

  const access = jar.get("mhc_access_token")?.value;
  if (!access) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const base =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";
  const res = await fetch(`${base}/api/v1/vms/${params.vmId}/${action}`, {
    method: "POST",
    headers: { authorization: `Bearer ${access}`, "content-type": "application/json" },
    body: JSON.stringify({ confirm: false })
  });

  const text = await res.text();
  return new NextResponse(text, { status: res.status, headers: { "content-type": "application/json" } });
}
