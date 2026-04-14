import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST() {
  const jar = cookies();
  jar.delete("mhc_demo");
  jar.delete("mhc_access_token");
  jar.delete("mhc_refresh_token");
  return NextResponse.json({ ok: true });
}

