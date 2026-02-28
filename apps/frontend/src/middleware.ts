import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token");
  const { pathname } = request.nextUrl;

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  // 로그인 상태에서 공개 경로 접근 시 /rooms로 리다이렉트
  if (isPublic && token) {
    return NextResponse.redirect(new URL("/rooms", request.url));
  }

  // 비로그인 → 보호 경로 접근 시 /login으로 리다이렉트
  if (!isPublic && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
