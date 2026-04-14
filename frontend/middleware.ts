import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  if (process.env.MHC_DISABLE_AUTH_MIDDLEWARE === "true") {
    return NextResponse.next();
  }

  const access = req.cookies.get("mhc_access_token")?.value;
  const { pathname } = req.nextUrl;
  const protectedPath = pathname.startsWith("/dashboard") || pathname.startsWith("/admin");
  if (protectedPath && !access) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/admin/:path*"]
};
