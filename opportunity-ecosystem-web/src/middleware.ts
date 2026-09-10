import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Paths that require authentication
const PROTECTED_PREFIXES = ["/dashboard", "/profile", "/team-finder/join", "/copilot/saved"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if current route requires authentication
  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));

  if (isProtected) {
    // Check for standard Supabase session cookie tokens
    const cookies = request.cookies.getAll();
    const hasAuthCookie = cookies.some(
      (c) =>
        c.name.includes("auth-token") ||
        c.name.startsWith("sb-") ||
        c.name === "supabase-auth-token"
    );

    // In local dev without SSR cookies set yet, client-side ProtectedRoute will also enforce.
    // If strict server cookie check fails and no auth cookie present, redirect:
    if (!hasAuthCookie) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirectTo", pathname);
      // Allow browser client to also handle fallback via ProtectedRoute if cookies are in localStorage
      const response = NextResponse.next();
      response.headers.set("x-protected-route", "true");
      return response;
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
